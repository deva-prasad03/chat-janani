from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from detoxify import Detoxify
import smtplib
from email.message import EmailMessage

#

EMAIL = "devaprasadsakthivel@gmail.com"
APP_PASSWORD = "mtua kyap dwcv gvzq"

# ---------------- App ----------------
app = FastAPI(
    title="English Toxicity Moderation API",
    version="1.0.0",
    description="FastAPI + Detoxify (original model)"
)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow all origins
    allow_credentials=False,    # MUST be False with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Model ----------------
model = Detoxify("original")  # load ONCE

# ---------------- Schemas ----------------
class TextRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="English text to be moderated"
    )

class ModerationResponse(BaseModel):
    toxic: bool
    scores: dict[str, float]

# ---------------- Endpoint ----------------
@app.post("/moderate", response_model=ModerationResponse)
def moderate_text(payload: TextRequest):
    text = payload.text.strip()

    if not text:
        raise HTTPException(400, "Text cannot be empty")

    if not text.isascii():
        raise HTTPException(400, "Only English text is supported")

    raw_scores = model.predict(text)

    # convert numpy floats → python floats
    scores = {k: float(v) for k, v in raw_scores.items()}

    toxic = (
        scores["toxicity"] > 0.7
        or scores["severe_toxicity"] > 0.5
        or scores["threat"] > 0.6
    )

    if(toxic):
        sendmail(text)

    return {
        "toxic": toxic,
        "scores": scores
    }

def sendmail(text):
    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = "devaprasadsakthivel@gmail.com"
    msg["Subject"] = "Harmfull word is find in your chat"
    msg.set_content(f"Harmful word is: {text}")

    msg.add_alternative(f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>🚨 Harmful Word Detected</h2>

        <p><strong>Detected Word:</strong></p>
        <p style="color:red; font-size:18px;">{text}</p>

        <br/>

        <a href="https://www.csk.gov.in/"
           style="padding:10px 20px;
                  background:#d9534f;
                  color:white;
                  text-decoration:none;
                  border-radius:5px;
                  margin-right:10px;">
           🚨 Send Report to Cyber Security
        </a>

        <a href="http://127.0.0.1:5500/chat.html"
           style="padding:10px 20px;
                  background:#5cb85c;
                  color:white;
                  text-decoration:none;
                  border-radius:5px;">
           ✅ Ignore
        </a>

        <br/><br/>
        <p style="font-size:12px;color:gray;">
          If no action is taken, the content will remain unchanged.
        </p>
      </body>
    </html>
    """, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

    print("Email sent!")