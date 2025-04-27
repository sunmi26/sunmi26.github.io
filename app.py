from flask import Flask, request, jsonify, render_template
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("input", "")
    prompt = request.json.get("prompt", "")
    if not user_input:
        return jsonify({"error": "输入不能为空，请提供有效的检测数据。"})
    try:
        pattern = r'(.+?)(?:（(\d{4}年\d{1,2}月(?:\d{1,2}日)?)）)?氡含量(\d+(?:\.\d+)?)Bq/L（历史(\d+(?:\.\d+)?)）水位(\d+(?:\.\d+)?)m（历史(\d+(?:\.\d+)?)）'
        match = re.match(pattern, user_input)
        if match:
            location = match.group(1).strip()
            time_range = match.group(2) if match.group(2) else "未提供"
            radon = float(match.group(3))
            radon_history = float(match.group(4))
            water_level = float(match.group(5))
            water_history = float(match.group(6))

            data = {
                "location": location,
                "time_range": time_range,
                "radon": {"value": radon, "history": radon_history},
                "water_level": {"value": water_level, "history": water_history}
            }
            result = analyze_groundwater(data, prompt)
            return render_template('result.html', result=result)
        else:
            return jsonify({
                "error": "输入格式错误，请按格式输入：地点（检测时间）氡含量X Bq/L（历史Y）水位Z m（历史W），例如：四川雅安（2025年4月）氡含量15.8Bq/L（历史10.2）水位12.5m（历史12.0）"
            })
    except Exception as e:
        return jsonify({"error": f"处理失败：{str(e)}"})

def analyze_groundwater(data, prompt):
    try:
        location = data.get("location", "")
        time_range = data.get("time_range", "")
        radon = data.get("radon", {}).get("value", 0)
        radon_history = data.get("radon", {}).get("history", 0)
        water_level = data.get("water_level", {}).get("value", 0)
        water_history = data.get("water_level", {}).get("history", 0)

        radon_change = (radon - radon_history) / radon_history * 100 if radon_history != 0 else 0
        water_change = (water_level - water_history) / water_history * 100 if water_history != 0 else 0

        risk_score = 0.4 * radon_change + 0.35 * water_change
        if risk_score < 30:
            risk_level = "绿色（低风险）"
        elif risk_score < 60:
            risk_level = "黄色（中等风险）"
        else:
            risk_level = "红色（高风险）"

        response = {
            "risk_level": risk_level,
            "score": f"{risk_score:.1f}分",
            "analysis": [
                f"氡含量：{radon}Bq/L（历史{radon_history}Bq/L，变化率{radon_change:.1f}%）",
                f"地下水位：{water_level}m（历史{water_history}m，变化率{water_change:.1f}%）"
            ],
            "suggestions": [
                "建议加密监测关键指标（每日至少2次）",
                "结合当地地质构造带位置综合分析",
                f"当前风险等级{risk_level}，请根据《地震监测应急预案》第{int(risk_score // 30) + 1}级响应处理"
            ]
        }

        # 根据提示词生成详细输出
        if "水质" in prompt:
            response["analysis"].append("水质分析：监测水质中化学成分的变化，如pH值、溶解氧等。")
        if "水温" in prompt:
            response["analysis"].append("水温分析：监测水温的异常变化，可能预示地震活动。")
        if "化学成分" in prompt:
            response["analysis"].append("化学成分分析：监测地下水中氡气等化学成分的突然增加。")

        return response
    except Exception as e:
        return {"error": f"数据解析失败：{str(e)}"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)    