import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv
import json

app = FastAPI()
# 載入 .env
load_dotenv()
 
#CORS跨來源設定
origins = ["http://localhost:5173"]  # 前端 Vite 開發地址
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 或 ["*"] 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



headers = {
    "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
     "Content-Type": "application/json"
}

#1.先把用戶輸入的文字翻譯成英文
def translate_to_en(chinese_text):
     translate_prompt = f"""
    請將以下繁體中文描述轉成「Stable Diffusion 圖像生成用的英文 prompt」。
    規則：
    - 只輸出英文
    - 使用關鍵字風格（不要完整句子）
    - 適合寫實 / 高品質插畫
    - 不要加任何解釋

    中文描述：
    {chinese_text}
    """
     payload = {
        "model": os.getenv("MODEL"),
        "messages": [
            {"role": "system", "content": "You are a professional prompt engineer for Stable Diffusion."},
            {"role": "user", "content": translate_prompt}
        ]
    }
     
     r = requests.post(os.getenv('CHAT_API_URL'), headers=headers, json=payload, timeout=60)
     data = r.json()
     try:
         return data["choices"][0]["message"]["content"].strip()
     except:
         return chinese_text  # 翻譯失敗則回傳原文

#2.把翻譯完的文字丟給圖片生成模型
def generate_image(prompt_zh):
    prompt_en = translate_to_en(prompt_zh)
    final_prompt = f"""{prompt_en}，
    masterpiece, best quality, ultra high resolution,highly detailed, photorealistic,
    cinematic lighting,volumetric lighting, depth of field,beautiful face, 
    realistic skin texture, 85mm lens, RAW photo, 8k"""
    r = requests.post(
        os.getenv('IMG_API_URL'),
        headers=headers,
        json={"inputs": final_prompt},
        timeout=60
    )
    if r.status_code != 200:
        return None
    return r.content


@app.post("/generate")
async def ai_image(request: Request):
    try:
        data = await request.json()
        prompt_zh = data.get("prompt", "")
        image_data = generate_image(prompt_zh)
        if image_data is None:
            return {"error": "圖片生成失敗"}
        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")  # 預設值
    port = int(os.getenv("PORT", 8000))    # 預設值

    uvicorn.run(app, host=host, port=port)