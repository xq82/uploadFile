
chunkSize = 5 * 1024 * 1024   //单个临时文件大小
const blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice;
function hashFile(file) {
  return new Promise((resolve, reject) => {
    const chunks = Math.ceil(file.size / chunkSize);
    let currentChunk = 0;
    const spark = new SparkMD5.ArrayBuffer();
    const fileReader = new FileReader();
    function loadNext() {
      const start = currentChunk * chunkSize;
      const end = start + chunkSize >= file.size ? file.size : start + chunkSize;
      fileReader.readAsArrayBuffer(blobSlice.call(file, start, end));
    }
    fileReader.onload = e => {
      spark.append(fileReader.result);
      currentChunk += 1;
      if (currentChunk < chunks) {
        loadNext();
      } else {
        const result = spark.end();
        const sparkMd5 = new SparkMD5();
        sparkMd5.append(result);
        const hexHash = sparkMd5.end();
        console.log("文件加载完毕， 准备上传.")
        resolve(hexHash)
      }
    };
    fileReader.onerror = () => {
      console.warn('文件读取失败！');
    };
    console.log("正在加载文件， 请等候 ...")
    loadNext();
  }).catch(err => {
    console.log(err);
  });
}


function ajax(method, url, data) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open(method, url, true)
    request.send(data)
    request.onreadystatechange = function () {
      if (request.readyState == 4 && request.status == 200) {
        resolve(request.responseText)
      }
    }

  })
}


async function upload_file_exists(file_name, md5V) {
  // 验证已经上传的文件是否存在
  formData = new FormData();
  formData.append("file_name", file_name)
  formData.append("md5V", md5V)
  return await ajax("POST", "/upload_file_exists", formData)
}


async function tmp_file_exists(tmp_file_name) {
  // 验证临时分片文件是否存在
  formData = new FormData();
  formData.append("file_name", tmp_file_name)
  return await ajax("POST", "/tmp_file_exists", formData)
}


async function upload_tmp_file(file, start, end, tmp_file_name) {
  formData = new FormData();
  formData.append('file', blobSlice.call(file, start, end))
  formData.append('file_name', tmp_file_name)
  return await ajax("POST", "/upload_tmp_file", formData)
}


async function merge_file(md5V, file_num, file_name) {
  formData = new FormData();
  formData.append('md5V', md5V)
  formData.append('file_num', file_num)
  formData.append('file_name', file_name)
  return await ajax("POST", "/merge_file", formData)
}


async function delete_tmp_file(md5V, file_num) {
  formData = new FormData();
  formData.append('md5V', md5V)
  formData.append('file_num', file_num)
  return await ajax("POST", "/delete_tmp_file", formData)
}

