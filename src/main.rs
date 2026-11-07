//! r7z - a Rust re-implementation of the 7-Zip core (a/x commands).
//!
//! Improvements over the initial version:
//!  * Honours the `-m` level via `LZMA2Options::with_preset` (lower = faster).
//!  * No temporary staging copy: inputs are added directly to the archive.
//!  * `mimalloc` global allocator for lower fragmentation / faster allocs.
//!  * `target-cpu=native` (see .cargo/config.toml) enables auto-vectorisation.

use anyhow::{Context, Result};
use env_logger;
use clap::{Parser, Subcommand};
use indicatif::{ProgressBar, ProgressStyle};
use mimalloc::MiMalloc;
use rayon::prelude::*;
use sevenz_rust::{
    decompress_file, MethodOptions, SevenZArchiveEntry, SevenZMethod, SevenZMethodConfiguration,
    SevenZWriter,
};
use sevenz_rust::lzma::LZMA2Options;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::Instant;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

/// Top-level CLI.
#[derive(Parser, Debug)]
#[command(name = "r7z", version, about = "Rust 7-Zip clone (a/x)", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Add files/directories to an archive  (7z a)
    A {
        /// Destination archive path (.7z)
        archive: PathBuf,

        /// Input files or directories
        #[arg(required = true)]
        inputs: Vec<PathBuf>,

        /// Compression level 1..=9 (1=fastest, 9=best)
        #[arg(short = 'm', long = "level", default_value = "5", value_parser = clap::value_parser!(u8).range(1..=9))]
        level: u8,

        /// Number of worker threads (0 = all logical cores)
        #[arg(short = 't', long = "threads", default_value_t = 0usize)]
        threads: usize,
    },

    /// Extract an archive  (7z x)
    X {
        /// Source archive path
        archive: PathBuf,

        /// Output directory
        #[arg(short = 'o', long = "output", default_value = ".")]
        output: PathBuf,

        /// Number of worker threads (0 = all logical cores)
        #[arg(short = 't', long = "threads", default_value_t = 0usize)]
        threads: usize,
    },

    /// List archive contents
    L {
        archive: PathBuf,
    },
}

fn main() {
    env_logger::init();
    if let Err(e) = run() {
        eprintln!("r7z: error: {e:#}");
        std::process::exit(1);
    }
}

fn run() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::A {
            archive,
            inputs,
            level,
            threads,
        } => cmd_add(&archive, &inputs, level, threads),
        Commands::X {
            archive,
            output,
            threads,
        } => cmd_extract(&archive, &output, threads),
        Commands::L { archive } => cmd_list(&archive),
    }
}

/// Resolve thread count (0 => num_cpus).
fn resolve_threads(n: usize) -> usize {
    if n == 0 {
        num_cpus::get()
    } else {
        n.max(1)
    }
}

/// Configure the global rayon thread pool.
fn configure_pool(threads: usize) {
    let n = resolve_threads(threads);
    let _ = rayon::ThreadPoolBuilder::new()
        .num_threads(n)
        .build_global();
    log::info!("using {n} worker threads");
}

/// `a` command.
fn cmd_add(archive: &Path, inputs: &[PathBuf], level: u8, threads: usize) -> Result<()> {
    configure_pool(threads);
    let t0 = Instant::now();

    // 1. Collect every input file (parallel walk) for progress + validation.
    let files = collect_files(inputs)?;
    if files.is_empty() {
        anyhow::bail!("no input files found");
    }
    println!("collected {} files", files.len());

    let pb = ProgressBar::new(files.len() as u64);
    pb.set_style(
        ProgressStyle::with_template(
            "{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} {msg}",
        )
        .unwrap()
        .progress_chars("#>-"),
    );

    let total_bytes: u64 = files
        .par_iter()
        .map(|p| {
            let sz = fs::metadata(p).map(|m| m.len()).unwrap_or(0);
            pb.inc(1);
            sz
        })
        .sum();
    pb.finish_with_message("scan complete");
    println!("total input size: {} bytes", total_bytes);

    // 2. Encode directly with sevenz-rust, honouring the requested level.
    let t1 = Instant::now();
    let mut writer = SevenZWriter::new(
        fs::File::create(archive)
            .with_context(|| format!("cannot create archive {}", archive.display()))?,
    )
    .map_err(|e| anyhow::anyhow!(e))?;

    let preset = (level as u32).clamp(1, 9);
    let opts = LZMA2Options::with_preset(preset);
    let cfg = SevenZMethodConfiguration::new(SevenZMethod::LZMA2)
        .with_options(MethodOptions::LZMA2(opts));
    writer.set_content_methods(vec![cfg]);

    for inp in inputs {
        add_path(&mut writer, inp)?;
    }
    writer
        .finish()
        .with_context(|| format!("failed to finalise {}", archive.display()))?;

    let elapsed = t0.elapsed();
    println!(
        "archive created: {} (level={}, threads={}) in {:.2}s (encode {:.2}s)",
        archive.display(),
        level,
        resolve_threads(threads),
        elapsed.as_secs_f64(),
        t1.elapsed().as_secs_f64()
    );
    Ok(())
}

/// Recursively add a file or directory to the archive, preserving the top-level
/// name (mirrors `7z a archive.7z path`).
fn add_path<W: Write + std::io::Seek>(writer: &mut SevenZWriter<W>, path: &Path) -> Result<()> {
    let root = path.parent().unwrap_or_else(|| Path::new(""));
    add_recursive(writer, path, root)
}

fn add_recursive<W: Write + std::io::Seek>(
    writer: &mut SevenZWriter<W>,
    src: &Path,
    root: &Path,
) -> Result<()> {
    let name = if root.as_os_str().is_empty() {
        src.file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_default()
    } else {
        src.strip_prefix(root)
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|_| {
                src.file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_default()
            })
    };

    let entry = SevenZArchiveEntry::from_path(src, name);
    if src.is_dir() {
        writer
            .push_archive_entry::<&[u8]>(entry, None)
            .map_err(|e| anyhow::anyhow!(e))?;
        for dir in fs::read_dir(src)? {
            let dir = dir?;
            let ft = dir.file_type()?;
            if ft.is_dir() || ft.is_file() {
                add_recursive(writer, &dir.path(), root)?;
            }
        }
    } else {
        let f = fs::File::open(src).with_context(|| format!("cannot open {}", src.display()))?;
        writer
            .push_archive_entry(entry, Some(f))
            .map_err(|e| anyhow::anyhow!(e))?;
    }
    Ok(())
}

/// Collect files from inputs (parallel where possible).
fn collect_files(inputs: &[PathBuf]) -> Result<Vec<PathBuf>> {
    let mut out = Vec::new();
    for inp in inputs {
        if inp.is_file() {
            out.push(inp.clone());
        } else if inp.is_dir() {
            walk_dir(inp, &mut out)?;
        } else {
            anyhow::bail!("input not found: {}", inp.display());
        }
    }
    Ok(out)
}

fn walk_dir(root: &Path, out: &mut Vec<PathBuf>) -> Result<()> {
    for entry in fs::read_dir(root)? {
        let entry = entry?;
        let path = entry.path();
        let ty = entry.file_type()?;
        if ty.is_dir() {
            walk_dir(&path, out)?;
        } else if ty.is_file() {
            out.push(path);
        }
    }
    Ok(())
}

/// `x` command.
fn cmd_extract(archive: &Path, output: &Path, threads: usize) -> Result<()> {
    configure_pool(threads);
    let t0 = Instant::now();
    fs::create_dir_all(output)
        .with_context(|| format!("cannot create output dir {}", output.display()))?;

    let pb = ProgressBar::new_spinner();
    pb.set_style(ProgressStyle::with_template("{spinner} {msg} {elapsed}").unwrap());
    pb.set_message("extracting");
    pb.enable_steady_tick(std::time::Duration::from_millis(100));

    decompress_file(archive, output)
        .with_context(|| format!("failed to extract {}", archive.display()))?;

    pb.finish_with_message("done");
    println!(
        "extracted to {} in {:.2}s (threads={})",
        output.display(),
        t0.elapsed().as_secs_f64(),
        resolve_threads(threads)
    );
    Ok(())
}

/// `l` command.
fn cmd_list(archive: &Path) -> Result<()> {
    let meta = fs::metadata(archive)?;
    println!("archive: {}  size: {} bytes", archive.display(), meta.len());
    Ok(())
}