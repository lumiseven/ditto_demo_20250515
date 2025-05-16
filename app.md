# Ditto TalkingHead API

本文档提供了Ditto TalkingHead API的概述，该API用于从音频和源图像/视频生成会说话的头像视频。

## API端点

### 1. 生成视频

**端点：** `/generate`  
**方法：** POST  
**描述：** 从音频和源图像/视频生成会说话的头像视频并返回供下载。

**参数：**

- `audio_file`：音频文件（.wav格式）
  - 可选
  - 如果未提供，默认为`./example/audio.wav`
  
- `source_file`：源图像或视频文件
  - 可选
  - 如果未提供，默认为`./example/image.png`
  
- `more_kwargs`：JSON字符串或pickle文件路径，包含额外参数
  - 可选

**响应：**
- 成功：返回生成的视频文件（MP4格式）
- 错误：返回状态码为500的JSON错误消息

### 2. 健康检查

**端点：** `/health`  
**方法：** GET  
**描述：** 简单的健康检查端点，用于验证API是否正常运行。

**响应：**
- 返回`{"status": "healthy"}`

## 使用示例

### 默认值测试

此示例使用默认的音频和源文件：

```bash
curl -X POST \
  'https://u305743-aac6-7ba70667.westb.seetacloud.com:8443/generate' \
  -H 'accept: application/json' \
  -F 'key1=value1' \
  -F 'key2=value2' \
  -o response1.mp4
```

**参数说明：**
- `-X POST`：指定POST请求
- `-H 'accept: application/json'`：设置Accept头为application/json
- `-F 'key1=value1' -F 'key2=value2'`：表单数据（注意：这些参数不被API使用，仅作示例展示）
- `-o response1.mp4`：将响应保存到名为response1.mp4的文件

### 自定义音频和源文件测试

此示例提供自定义音频和源文件：

```bash
curl -X POST \
  'https://u305743-aac6-7ba70667.westb.seetacloud.com:8443/generate' \
  -H "accept: application/json" \
  -F "audio_file=@./example/audio.wav" \
  -F "source_file=@./example/image.png" \
  -o response2.mp4
```

**参数说明：**
- `-X POST`：指定POST请求
- `-H "accept: application/json"`：设置Accept头为application/json
- `-F "audio_file=@./example/audio.wav"`：上传自定义音频文件（@符号表示文件上传）
- `-F "source_file=@./example/image.png"`：上传自定义源图像文件
- `-o response2.mp4`：将响应保存到名为response2.mp4的文件
