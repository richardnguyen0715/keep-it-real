import time
import ray

# 1. Khởi tạo Ray (nếu chạy trên máy tính cá nhân, Ray sẽ tự động tận dụng toàn bộ số CPU bạn có)
ray.init()

# Giả lập một tác vụ nặng tốn 1 giây để xử lý (như đọc file, tính toán AI...)
def task_thong_thuong(x):
    time.sleep(1)
    return x * x

# 2. Thêm decorator @ray.remote để biến hàm bình thường thành một Ray Task
@ray.remote
def task_ray(x):
    time.sleep(1)
    return x * x

if __name__ == "__main__":
    print("--- CHẠY THỬ NGHIỆM KHÔNG DÙNG RAY ---")
    start_time = time.time()
    # Chạy tuần tự 4 tác vụ (tốn 4 giây)
    ket_qua_thuong = [task_thong_thuong(i) for i in range(4)]
    print(f"Kết quả thường: {ket_qua_thuong}")
    print(f"Thời gian chạy thường: {time.time() - start_time:.2f} giây\n")


    print("--- CHẠY THỬ NGHIỆM CÓ DÙNG RAY ---")
    start_time = time.time()
    
    # Kích hoạt 4 tác vụ chạy song song cùng lúc bằng cách thêm `.remote()`
    # Lúc này Ray không trả về kết quả ngay mà trả về các Object Ref (gọi là tương lai/futures)
    object_refs = [task_ray.remote(i) for i in range(4)]
    
    # Dùng ray.get() để gom tất cả kết quả về khi các máy/CPU đã tính toán xong
    ket_qua_ray = ray.get(object_refs)
    
    print(f"Kết quả với Ray: {ket_qua_ray}")
    print(f"Thời gian chạy với Ray: {time.time() - start_time:.2f} giây")

    # Ngắt kết nối Ray sau khi dùng xong
    ray.shutdown()