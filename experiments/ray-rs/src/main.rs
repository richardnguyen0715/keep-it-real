use rayon::prelude::*;
use std::thread;
use std::time::{Duration, Instant};

fn task(x: i32) -> i32 {
    thread::sleep(Duration::from_secs(1));
    x * x
}

fn main() {
    println!("--- CHẠY THỬ NGHIỆM KHÔNG DÙNG RUST RAYON ---");
    let start = Instant::now();
    let results_seq: Vec<i32> = (0..4).map(|i| task(i)).collect();
    println!("Kết quả thường: {:?}", results_seq);
    println!("Thời gian chạy thường: {:.2} giây\n", start.elapsed().as_secs_f64());

    println!("--- CHẠY THỬ NGHIỆM CÓ DÙNG RUST RAYON ---");
    let start = Instant::now();
    let inputs: Vec<i32> = (0..4).collect();
    let results_par: Vec<i32> = inputs.par_iter().map(|&i| task(i)).collect();
    println!("Kết quả với Rayon: {:?}", results_par);
    println!("Thời gian chạy với Rayon: {:.2} giây", start.elapsed().as_secs_f64());
}
