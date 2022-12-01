import os, json
from threading import RLock
from hashlib import md5
from flask import request, render_template, Flask, url_for

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(path, "  文件夹创建成功")


DIR = os.path.abspath(os.path.join(__file__, ".."))  # 如果要打包为exe文件  则 DIR = os.getcwd()

FILE_INDEX = "file_dir"   #合并后文件保存路径
TMP_FILES = "tmp_dir"   #临时文件存放路径
JSON_PATH = "md5v.json"    #文件哈希保存json
STATIC_DIR = "static"      # 静态文件保存路径（js css img 存放路径）

STATIC_DIR = os.path.join(DIR, STATIC_DIR)

FILE_INDEX = os.path.join(STATIC_DIR, FILE_INDEX)
TMP_FILES = os.path.join(STATIC_DIR, TMP_FILES)
JSON_PATH = os.path.join(STATIC_DIR, JSON_PATH)
mkdir(STATIC_DIR)
mkdir(FILE_INDEX)
mkdir(TMP_FILES)
print("静态文件夹路径 ", STATIC_DIR)
print("最终合并的文件文件夹路径 ", FILE_INDEX)
print("分片文件文件夹路径 ", TMP_FILES)



file_hash = lambda file: md5(file).hexdigest()
lock = RLock()
app = Flask(__name__,  static_folder=STATIC_DIR)


def read_json(json_path=JSON_PATH):
    if not os.path.exists(json_path):
        json_data = {}
        list_dir = os.listdir(FILE_INDEX)
        for i in list_dir:
            with open(os.path.join(FILE_INDEX, i), "rb") as f:
                md5v = file_hash(f.read())
            if  json_data.get(md5v):
                json_data[md5v].append(i)
            else:
                json_data[md5v] = [i]
        save_json(json_data)
        return json_data
    else:
        lock.acquire(timeout=10, blocking=True)
        with open(json_path, "r", encoding="utf-8") as f:
            data = f.read()
        lock.release()
        return json.loads(data)


def save_json(json_data, json_path=JSON_PATH):
    if isinstance(json_data, dict):
        json_data = json.dumps(json_data, ensure_ascii=False)
    lock.acquire(timeout=10, blocking=True)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_data)
    lock.release()
    return json_data


def file_exists(file, dir):
    """验证文件是否存在"""
    path = os.path.join(dir, file)
    if os.path.exists(path):
        return path
    return None


def merge_md5_file(md5V, file_num, file_name):
    """合并md5临时文件"""
    try:
        lock.acquire(timeout=10, blocking=True)
        json_data = read_json()
        if json_data.get(md5V):
            return "文件合并成功"
        for i in range(file_num):
            with open(os.path.join(TMP_FILES, f"{md5V}_{i}.tmp"), "rb") as f:
                tmp_file = f.read()
            with open(os.path.join(FILE_INDEX, file_name), "ab+") as f:
                f.write(tmp_file)
        json_data[md5V] = []
        json_data[md5V].append(file_name)
        save_json(json_data)
        lock.release()
        return "文件合并成功"
    except Exception as e:
        return "文件合并失败 "  + str(e)


def del_tmp_file(md5V, file_num):
    try:
        for i in range(file_num):
            tmp_file = os.path.join(TMP_FILES, f"{md5V}_{i}.tmp")
            os.remove(tmp_file)
        return "分片文件删除完毕"
    except Exception as e:
        return "文件删除失败  " + str(e)


@app.route("/upload_file_exists", methods=["POST"])
def upload_file_exists():
    """验证已上传的文件是否存在"""
    file_name = request.form.get("file_name")
    md5v =  request.form.get("md5V")
    md5Vs = read_json()
    if md5Vs.get(md5v):
        if file_name not in md5Vs.get(md5v):
            md5Vs[md5v].append(file_name)
            save_json(md5Vs)
        return "已存在"
    return "不存在"


@app.route("/tmp_file_exists", methods=["POST"])
def tmp_file_exists():
    """验证分片文件是否存在"""
    file_name = request.form.get("file_name")
    if  file_exists(file_name, TMP_FILES):
        return "已存在"
    return "不存在"


@app.route("/upload_tmp_file", methods=["POST"])
def upload_tmp_file():
    """保存上传的临时文件 加锁处理"""
    file = request.files["file"]
    file_name = request.form.get("file_name")
    file_dir = os.path.join(TMP_FILES, file_name)
    if not os.path.exists(file_dir):
        #加锁防止产生混乱
        lock.acquire(timeout=10, blocking=True)
        with open(file_dir, "wb") as f:
            f.write(file.read())
        lock.release()
        return file_name + " 上传成功"
    return file_name + " 已存在"


@app.route("/merge_file", methods=["POST"])
def merge_file():
    md5V, file_num, file_name = request.form.get("md5V"), request.form.get("file_num"), request.form.get("file_name")
    return merge_md5_file(md5V, int(file_num), file_name)


@app.route("/delete_tmp_file", methods=["POST", "GET"])
def delete_tmp_file():
    md5V, file_num = request.form.get("md5V"), request.form.get("file_num")
    return del_tmp_file(md5V, int(file_num))


@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("./index.html")


if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0", threaded=True)