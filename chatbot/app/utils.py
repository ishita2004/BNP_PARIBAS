import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
from datetime import datetime

def df_to_bar_chart(df, x_col, y_col):
    plt.figure(figsize=(8,5))
    plt.bar(df[x_col], df[y_col])
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def log_error(message):
    log_dir = "app/logs"
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "error.log"), "a") as f:
        f.write(f"{datetime.now()} - {message}\n")
