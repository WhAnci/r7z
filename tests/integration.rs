use std::fs;
use std::process::Command;

#[test]
fn roundtrip_compress_extract() {
    let tmp = std::env::temp_dir().join("r7z_test_roundtrip");
    let _ = fs::remove_dir_all(&tmp);
    fs::create_dir_all(tmp.join("in")).unwrap();
    fs::write(tmp.join("in/hello.txt"), b"hello world\n").unwrap();
    fs::write(tmp.join("in/data.bin"), vec![0u8, 1, 2, 3, 4]).unwrap();

    let archive = tmp.join("out.7z");
    let bin = env!("CARGO_BIN_EXE_r7z");

    let status = Command::new(bin)
        .args(["a", archive.to_str().unwrap(), tmp.join("in").to_str().unwrap(), "-m", "5", "-t", "2"])
        .status()
        .expect("run r7z a");
    assert!(status.success(), "compress failed");

    let extracted = tmp.join("extracted");
    let status = Command::new(bin)
        .args(["x", archive.to_str().unwrap(), "-o", extracted.to_str().unwrap(), "-t", "2"])
        .status()
        .expect("run r7z x");
    assert!(status.success(), "extract failed");

    let hello = fs::read_to_string(extracted.join("hello.txt")).unwrap();
    assert_eq!(hello, "hello world\n");
    let data = fs::read(extracted.join("data.bin")).unwrap();
    assert_eq!(data, vec![0u8, 1, 2, 3, 4]);

    let _ = fs::remove_dir_all(&tmp);
}

#[test]
fn list_command() {
    let tmp = std::env::temp_dir().join("r7z_test_list");
    let _ = fs::remove_dir_all(&tmp);
    fs::create_dir_all(tmp.join("in")).unwrap();
    fs::write(tmp.join("in/a.txt"), b"a").unwrap();
    let archive = tmp.join("out.7z");
    let bin = env!("CARGO_BIN_EXE_r7z");
    Command::new(bin)
        .args(["a", archive.to_str().unwrap(), tmp.join("in").to_str().unwrap()])
        .status()
        .unwrap();
    let out = Command::new(bin)
        .args(["l", archive.to_str().unwrap()])
        .output()
        .unwrap();
    assert!(out.status.success());
    assert!(String::from_utf8_lossy(&out.stdout).contains("archive:"));
    let _ = fs::remove_dir_all(&tmp);
}