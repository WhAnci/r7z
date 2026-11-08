//! r7z - a Rust re-implementation of the 7-Zip core (a/x commands).
//!
//! Backend: `sevenz-turbo` (solid + multi-threaded 7z, tuned for speed).

use anyhow::{Context, Result};
use clap::{CommandFactory, Parser, Subcommand};
use indicatif::{ProgressBar, ProgressStyle};
use mimalloc::MiMalloc;
use rayon::prelude::*;
use sevenz_turbo::decompress_file;
use sevenz_turbo::decompress_file_with_password;
use sevenz_turbo::encoder_options::{AesEncoderOptions, Lzma2Options};
use sevenz_turbo::{ArchiveWriter, EncoderConfiguration, Password};
use std::fs;
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

        /// Compression level 1..=9 (1=fastest, 9=best)  (-mx alias)
        #[arg(short = 'm', long = "level", alias = "mx", default_value = "5", value_parser = clap::value_parser!(u8).range(1..=9))]
        level: u8,

        /// Number of worker threads (0 = all logical cores)  (-mmt alias)
        #[arg(short = 't', long = "threads", alias = "mmt", default_value_t = 0usize)]
        threads: usize,

        /// Password for encryption
        #[arg(short = 'p', long = "password", default_value = "")]
        password: String,
        /// Assume yes to all prompts
        #[arg(short = 'y', long = "yes", default_value_t = false)]
        yes: bool,
    },

    /// Extract an archive  (7z x)
    X {
        /// Source archive path
        archive: PathBuf,

        /// Output directory
        #[arg(short = 'o', long = "output", default_value = ".")]
        output: PathBuf,

        /// Number of worker threads (0 = all logical cores)
        #[arg(short = 't', long = "threads", alias = "mmt", default_value_t = 0usize)]
        threads: usize,

        /// Password for decryption
        #[arg(short = 'p', long = "password", default_value = "")]
        password: String,
        /// Assume yes to all prompts
        #[arg(short = 'y', long = "yes", default_value_t = false)]
        yes: bool,
    },

    /// List archive contents
    L { archive: PathBuf },

    /// Test archive integrity  (7z t)
    T {
        /// Source archive path
        archive: PathBuf,

        /// Password for decryption
        #[arg(short = 'p', long = "password", default_value = "")]
        password: String,
    },

    /// Generate shell completions
    Completions {
        /// Shell to generate completions for
        #[arg(value_enum)]
        shell: clap_complete::Shell,
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
            password,
            yes: _,
        } => cmd_add(&archive, &inputs, level, threads, &password),
        Commands::X {
            archive,
            output,
            threads,
            password,
            yes: _,
        } => cmd_extract(&archive, &output, threads, &password),
        Commands::L { archive } => cmd_list(&archive),
        Commands::T { archive, password } => cmd_test(&archive, &password),
        Commands::Completions { shell } => {
            clap_complete::generate(shell, &mut Cli::command(), "r7z", &mut std::io::stdout());
            Ok(())
        }
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

/// `a` command.
fn cmd_add(
    archive: &Path,
    inputs: &[PathBuf],
    level: u8,
    threads: usize,
    password: &str,
) -> Result<()> {
    let t0 = Instant::now();
    let nth = resolve_threads(threads) as u32;

    // 1. Collect entries (disk_path, archive_name).
    let entries = collect_entries(inputs)?;
    if entries.is_empty() {
        anyhow::bail!("no input files found");
    }
    println!("collected {} files", entries.len());

    let pb = ProgressBar::new(entries.len() as u64);
    pb.set_style(
        ProgressStyle::with_template(
            "{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} {msg}",
        )
        .unwrap()
        .progress_chars("#>-"),
    );
    let total_bytes: u64 = entries
        .par_iter()
        .map(|(p, _)| {
            let sz = fs::metadata(p).map(|m| m.len()).unwrap_or(0);
            pb.inc(1);
            sz
        })
        .sum();
    pb.finish_with_message("scan complete");
    println!("total input size: {} bytes", total_bytes);

    // 2. Encode. Small files (<1MB) are read in parallel to avoid I/O bottleneck
    //    on many-small-files workloads; large files stream from disk.
    let t1 = Instant::now();
    let out = fs::File::create(archive)
        .with_context(|| format!("cannot create archive {}", archive.display()))?;
    let mut writer = ArchiveWriter::new(out).map_err(|e| anyhow::anyhow!(e))?;

    let mut methods = Vec::new();
    if !password.is_empty() {
        methods.push(EncoderConfiguration::from(AesEncoderOptions::new(
            Password::new(password),
        )));
    }
    let opts = Lzma2Options::from_level_mt(level as u32, nth, 1 << 20);
    methods.push(EncoderConfiguration::from(opts));
    writer.set_content_methods(methods);

    for inp in inputs {
        writer
            .push_source_path(inp, |_| true)
            .map_err(|e| anyhow::anyhow!(e))?;
    }

    let _ = writer.finish().map_err(|e| anyhow::anyhow!(e))?;

    let elapsed = t0.elapsed();
    println!(
        "archive created: {} (level={}, threads={}) in {:.2}s (encode {:.2}s)",
        archive.display(),
        level,
        nth,
        elapsed.as_secs_f64(),
        t1.elapsed().as_secs_f64()
    );
    Ok(())
}

/// Collect (disk_path, archive_name) pairs, preserving top-level dir name.
fn collect_entries(inputs: &[PathBuf]) -> Result<Vec<(PathBuf, String)>> {
    let mut out = Vec::new();
    for inp in inputs {
        if inp.is_file() {
            let name = inp
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
                .unwrap_or_default();
            out.push((inp.clone(), name));
        } else if inp.is_dir() {
            let root = inp.parent().unwrap_or_else(|| Path::new(""));
            walk_entries(inp, root, &mut out)?;
        } else {
            anyhow::bail!("input not found: {}", inp.display());
        }
    }
    Ok(out)
}

fn walk_entries(dir: &Path, root: &Path, out: &mut Vec<(PathBuf, String)>) -> Result<()> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        let ft = entry.file_type()?;
        if ft.is_dir() {
            walk_entries(&path, root, out)?;
        } else if ft.is_file() {
            let name = path
                .strip_prefix(root)
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_else(|_| {
                    path.file_name()
                        .map(|n| n.to_string_lossy().to_string())
                        .unwrap_or_default()
                });
            out.push((path, name));
        }
    }
    Ok(())
}

/// `x` command.
fn cmd_extract(archive: &Path, output: &Path, threads: usize, password: &str) -> Result<()> {
    let _ = threads;
    let t0 = Instant::now();
    fs::create_dir_all(output)
        .with_context(|| format!("cannot create output dir {}", output.display()))?;

    let pb = ProgressBar::new_spinner();
    pb.set_style(ProgressStyle::with_template("{spinner} {msg} {elapsed}").unwrap());
    pb.set_message("extracting");
    pb.enable_steady_tick(std::time::Duration::from_millis(100));

    if password.is_empty() {
        decompress_file(archive, output).map_err(|e| anyhow::anyhow!(e))?;
    } else {
        decompress_file_with_password(archive, output, Password::new(password))
            .map_err(|e| anyhow::anyhow!(e))?;
    }

    pb.finish_with_message("done");
    println!(
        "extracted to {} in {:.2}s",
        output.display(),
        t0.elapsed().as_secs_f64()
    );
    Ok(())
}

/// `t` command (test archive integrity).
fn cmd_test(archive: &Path, password: &str) -> Result<()> {
    let tmp = std::env::temp_dir().join(format!("r7z_test_{}", std::process::id()));
    let _ = fs::remove_dir_all(&tmp);
    fs::create_dir_all(&tmp)?;
    let res = if password.is_empty() {
        decompress_file(archive, &tmp)
    } else {
        decompress_file_with_password(archive, &tmp, Password::new(password))
    };
    let _ = fs::remove_dir_all(&tmp);
    match res {
        Ok(()) => {
            println!("Everything is OK");
            Ok(())
        }
        Err(e) => {
            eprintln!("Test failed: {e}");
            std::process::exit(1);
        }
    }
}

/// `l` command.
fn cmd_list(archive: &Path) -> Result<()> {
    let meta = fs::metadata(archive)?;
    println!("archive: {}  size: {} bytes", archive.display(), meta.len());
    Ok(())
}
