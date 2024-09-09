FROM python:3.11-slim

ENV PORT=8501
EXPOSE $PORT

WORKDIR /naob

COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD streamlit run app.py --server.port ${PORT} --server.baseUrlPath /naob --browser.gatherUsageStats=False
