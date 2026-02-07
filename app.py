import gradio as gr
import os
import json
import hashlib
import warnings
import threading
import queue
from datetime import datetime
import uuid

# 屏蔽无关警告
warnings.filterwarnings("ignore")

# ===================== 平台核心配置（研精豆品牌定版） =====================
PLATFORM_NAME_CN = "研精豆"
PLATFORM_NAME_EN = "Yanjingdou"
CONCLUSION_BG_COLOR = "#f0f8ff"
CONFIG_PATH = "/Users/weiwei.yao/Desktop/zhibian-verify/config.txt"
USER_DATA_PATH = "/Users/weiwei.yao/Desktop/zhibian-verify/user_data.json"
FREE_USE_LIMIT = 3
THREAD_TIMEOUT = 30
CURRENT_VERSION = "v1.4"  # 当前版本号

# ===================== 1. 用户数据管理 =====================
def init_user_data():
    """初始化用户数据文件"""
    if not os.path.exists(USER_DATA_PATH):
        init_data = {"users": {}, "guest_usage": {}}
        with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(init_data, f, ensure_ascii=False, indent=2)
    print(f"✅ {PLATFORM_NAME_CN} 用户数据文件初始化完成")

def load_user_data():
    """加载用户数据"""
    init_user_data()
    try:
        with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取用户数据失败：{e}")
        return {"users": {}, "guest_usage": {}}

def save_user_data(data):
    """保存用户数据"""
    try:
        with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ 保存用户数据失败：{e}")
        return False

def encrypt_password(password):
    """密码加密（MD5）"""
    return hashlib.md5(password.encode("utf-8")).hexdigest()

# ===================== 2. 注册/登录/游客模式逻辑 =====================
def user_register(username, password, confirm_pwd):
    """用户注册"""
    if not username or not password or not confirm_pwd:
        return "❌ 用户名/密码不能为空！", gr.update(value=""), gr.update(value="")
    if password != confirm_pwd:
        return "❌ 两次密码输入不一致！", gr.update(value=""), gr.update(value="")
    if len(password) < 6:
        return "❌ 密码长度不能少于6位！", gr.update(value=""), gr.update(value="")
    
    user_data = load_user_data()
    if username in user_data["users"]:
        return "❌ 用户名已存在！", gr.update(value=""), gr.update(value="")
    
    user_data["users"][username] = {
        "password": encrypt_password(password),
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usage_count": 0
    }
    
    if save_user_data(user_data):
        return "✅ 注册成功！请登录使用", gr.update(value=""), gr.update(value="")
    else:
        return "❌ 注册失败，请重试！", gr.update(value=""), gr.update(value="")

def user_login(username, password, user_state, guest_id_state):
    """用户登录"""
    if not username or not password:
        return "❌ 用户名/密码不能为空！", user_state, guest_id_state
    
    user_data = load_user_data()
    if username not in user_data["users"]:
        return "❌ 用户名不存在！", user_state, guest_id_state
    
    if user_data["users"][username]["password"] != encrypt_password(password):
        return "❌ 密码错误！", user_state, guest_id_state
    
    user_state = {"is_login": True, "username": username, "is_guest": False}
    return f"✅ 欢迎回来，{username}！", user_state, guest_id_state

def guest_mode(user_state, guest_id_state):
    """游客模式（3次免费）"""
    if not guest_id_state:
        guest_id = str(uuid.uuid4())[:8]
        guest_id_state = guest_id
        
        user_data = load_user_data()
        if guest_id not in user_data["guest_usage"]:
            user_data["guest_usage"][guest_id] = {
                "usage_count": 0,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_user_data(user_data)
    
    user_state = {"is_login": True, "username": f"游客{guest_id_state}", "is_guest": True}
    
    user_data = load_user_data()
    used_count = user_data["guest_usage"][guest_id_state]["usage_count"]
    remain_count = FREE_USE_LIMIT - used_count
    
    return f"✅ 游客模式已开启！剩余免费次数：{remain_count}次", user_state, guest_id_state

def logout(user_state, guest_id_state):
    """退出登录"""
    user_state = {"is_login": False, "username": "", "is_guest": False}
    guest_id_state = ""
    return "✅ 已退出登录！", user_state, guest_id_state

# ===================== 3. 配置文件读取 =====================
def load_config():
    config = {}
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ {PLATFORM_NAME_CN} 配置文件不存在：{CONFIG_PATH}")
        return config
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
        print(f"✅ {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 配置加载成功")
    except Exception as e:
        print(f"❌ {PLATFORM_NAME_CN} 配置文件读取失败：{str(e)}")
    return config

config = load_config()
TONGYI_API_KEY = config.get("TONGYI_API_KEY", "")
ZHIPU_API_KEY = config.get("ZHIPU_API_KEY", "")

# ===================== 4. 模型初始化 =====================
# 通义千问初始化
try:
    import dashscope
    from dashscope import Generation
    dashscope.api_key = TONGYI_API_KEY
    TONGYI_INIT_OK = True
except Exception as e:
    print(f"❌ {PLATFORM_NAME_CN} 通义千问初始化失败：{str(e)}")
    TONGYI_INIT_OK = False

# 智谱清言初始化
try:
    from zhipuai import ZhipuAI
    zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
    ZHIPU_INIT_OK = True
except Exception as e:
    print(f"❌ {PLATFORM_NAME_CN} 智谱清言初始化失败：{str(e)}")
    ZHIPU_INIT_OK = False

# ===================== 5. 裁判Prompt =====================
NEUTRAL_JUDGE_PROMPT = """请作为**无立场的中立学术裁判**，对答案进行研精析微式精准研判，严格遵守以下规则：
1. 判错唯一标准：答案存在**计算错误/知识点错误/逻辑漏洞/遗漏问题要求/结论与正确结果相悖**，无上述问题则标注「无明显错误」；
2. 严禁编造/虚构错误，严禁过度挑剔，判定需基于问题要求与客观事实；
3. 有错误时，需明确标注「错误类型+具体错误点+正确内容」，错误类型仅限：计算错误、知识点错误、逻辑错误、遗漏条件、结论错误；
4. 核心结论：提炼答案的**核心步骤+最终结果**，保留关键计算/推理过程，表述简洁精准；
5. 输出严格按以下格式，无多余文字、无注释、无补充说明：
错误标注：xxx
核心结论：xxx"""

# ===================== 6. 模型调用 =====================
def call_tongyi_answer(question, result_queue):
    if not TONGYI_INIT_OK:
        result_queue.put(("tongyi_ans", "研精千问初始化失败，无法答题"))
        return
    try:
        prompt = f"针对问题【{question}】，给出准确、简洁的答案，涉及计算/推理必须分步列出过程，不要多余文字。"
        response = Generation.call(
            model="qwen-turbo",
            prompt=prompt,
            result_format="text",
            temperature=0.1
        )
        result_queue.put(("tongyi_ans", f"研精千问作答：\n{response.output.text.strip()}"))
    except Exception as e:
        result_queue.put(("tongyi_ans", f"研精千问调用失败：{str(e)}"))

def call_zhipu_answer(question, result_queue):
    if not ZHIPU_INIT_OK:
        result_queue.put(("zhipu_ans", "研精清言初始化失败，无法答题"))
        return
    try:
        prompt = f"针对问题【{question}】，给出准确、简洁的答案，涉及计算/推理必须分步列出过程，不要多余文字。"
        messages = [{"role": "user", "content": prompt}]
        response = zhipu_client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            temperature=0.1
        )
        result_queue.put(("zhipu_ans", f"研精清言作答：\n{response.choices[0].message.content.strip()}"))
    except Exception as e:
        result_queue.put(("zhipu_ans", f"研精清言调用失败：{str(e)}"))

def neutral_judge_tongyi(question, answer, result_queue, judge_name):
    if not TONGYI_INIT_OK:
        result_queue.put((judge_name, "研精裁判初始化失败"))
        return
    try:
        prompt = f"{NEUTRAL_JUDGE_PROMPT}\n问题：{question}\n答案：{answer}"
        response = Generation.call(
            model="qwen-plus",
            prompt=prompt,
            result_format="text",
            temperature=0.0
        )
        result_queue.put((judge_name, response.output.text.strip()))
    except Exception as e:
        result_queue.put((judge_name, f"研精裁判调用失败：{str(e)}"))

def neutral_judge_zhipu(question, answer, result_queue, judge_name):
    if not ZHIPU_INIT_OK:
        result_queue.put((judge_name, "研精裁判初始化失败"))
        return
    try:
        prompt = f"{NEUTRAL_JUDGE_PROMPT}\n问题：{question}\n答案：{answer}"
        messages = [{"role": "user", "content": prompt}]
        response = zhipu_client.chat.completions.create(
            model="glm-4",
            messages=messages,
            temperature=0.0
        )
        result_queue.put((judge_name, response.choices[0].message.content.strip()))
    except Exception as e:
        result_queue.put((judge_name, f"研精裁判调用失败：{str(e)}"))

# ===================== 7. 工具函数 =====================
def get_error(judgment):
    lines = judgment.split("\n")
    for line in lines:
        if line.startswith("错误标注："):
            return line.replace("错误标注：", "").strip()
    return "无明显错误"

def get_conclusion(judgment):
    lines = judgment.split("\n")
    for line in lines:
        if line.startswith("核心结论："):
            return line.replace("核心结论：", "").strip()
    return "无有效结论"

def is_judge_consistent(j1, j2):
    err1, err2 = get_error(j1), get_error(j2)
    con1 = get_conclusion(j1).replace(" ", "").replace("\n", "").strip()[:100]
    con2 = get_conclusion(j2).replace(" ", "").replace("\n", "").strip()[:100]
    return err1 == err2 and con1 == con2

# ===================== 8. 共识融合（新增直接回答问题功能） =====================
def fuse_consensus(question, tongyi_ans, zhipu_ans, jt_t, jt_z, jz_t, jz_z):
    # 提取错误标注和核心结论
    tongyi_error1, tongyi_error2 = get_error(jt_t), get_error(jt_z)
    zhipu_error1, zhipu_error2 = get_error(jz_t), get_error(jz_z)
    tongyi_con = get_conclusion(jt_t)
    zhipu_con = get_conclusion(jz_t)
    
    # 判定最终错误类型和可信度等级
    tongyi_final_error = tongyi_error1 if is_judge_consistent(jt_t, jt_z) else "无明显错误"
    zhipu_final_error = zhipu_error1 if is_judge_consistent(jz_t, jz_z) else "无明显错误"
    
    if tongyi_final_error == "无明显错误" and zhipu_final_error == "无明显错误":
        credibility = "高可信度"
        # 双模型无错误，直接整合为统一回答
        direct_answer = f"{tongyi_con}"
        model_analysis = "双模型答案一致且均无错误，整合核心结论如下："
    elif tongyi_final_error != "无明显错误" and zhipu_final_error != "无明显错误":
        credibility = "低可信度"
        # 双模型均有错误，基于裁判修正后给出回答
        direct_answer = f"根据裁判修正结果，问题的合理答案为：{get_conclusion(jt_t) if tongyi_con else get_conclusion(jz_t)}"
        model_analysis = "双模型均存在错误，结合裁判修正结论如下："
    else:
        credibility = "中可信度"
        # 单模型无错误，优先采用无错误模型结论
        reliable_con = tongyi_con if tongyi_final_error == "无明显错误" else zhipu_con
        direct_answer = reliable_con
        model_analysis = f"{'研精千问' if tongyi_final_error == '无明显错误' else '研精清言'}答案无错误，核心结论如下："
    
    # 深度研精分析（保留原逻辑）
    if credibility == "高可信度":
        analysis = f"双模型答案一致且均无错误，最终结果：{direct_answer}"
    else:
        analysis = f"研精千问结论：{tongyi_con}；研精清言结论：{zhipu_con}；建议优先参考{model_analysis[:4]}的结论。"
    
    # 终审结论样式（新增「直接回应问题」模块，放在最顶部）
    styled_judgment = f"""
<div style="background-color: {CONCLUSION_BG_COLOR}; padding: 20px; border-radius: 8px; margin: 10px 0; border: 1px solid #d0e8ff; color: #333; word-wrap: break-word; word-break: break-all;">
  <h3 style="margin: 0 0 15px 0; color: #0056b3; font-weight: 600; font-size: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
    {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 终审结论 
    <span style="font-size: 12px; color: #666; font-weight: normal;">(AI生成内容，基于双模型研精析微)</span>
    <span style="font-family: 'SimHei', '黑体', sans-serif; font-weight: bold; color: #d9534f; font-size: 15px;">可信度评级：{credibility}</span>
  </h3>
  <!-- 新增：直接回应问题的答案（放在最前面，优先展示） -->
  <div style="margin: 0 0 15px 0; padding: 15px; background-color: #ffffff; border-radius: 6px; border: 1px solid #e8f4f8;">
    <h4 style="margin: 0 0 8px 0; color: #007bff; font-size: 14px;">🎯 直接回应问题</h4>
    <p style="margin: 0; line-height: 1.8; font-size: 14px; color: #222; font-weight: 500;">{direct_answer}</p>
  </div>
  <!-- 原有：深度研精分析 -->
  <p style="margin: 0; line-height: 1.8; font-size: 14px; color: #333;"><strong>📊 深度研精分析：</strong>{analysis}</p>
</div>
"""
    return styled_judgment

# ===================== 9. 核心业务逻辑 =====================
def core_verify_logic(question, user_state, guest_id_state):
    # 1. 登录状态校验
    if not user_state or not user_state.get("is_login"):
        yield gr.update(value="❌ 请先登录或使用游客模式！"), gr.update(
            variant="primary",
            interactive=True,
            value="提交研精验证"
        ), user_state, guest_id_state
        return
    
    # 2. 空问题校验
    if not question.strip():
        yield gr.update(value="❌ 请输入有效的问题！"), gr.update(
            variant="primary",
            interactive=True,
            value="提交研精验证"
        ), user_state, guest_id_state
        return
    
    # 3. 游客次数限制校验
    if user_state.get("is_guest"):
        user_data = load_user_data()
        guest_id = user_state["username"].replace("游客", "")
        
        if guest_id not in user_data["guest_usage"]:
            user_data["guest_usage"][guest_id] = {"usage_count": 0}
        
        used_count = user_data["guest_usage"][guest_id]["usage_count"]
        if used_count >= FREE_USE_LIMIT:
            yield gr.update(value=f"❌ 免费使用次数已用尽（共{FREE_USE_LIMIT}次），请注册账号后继续使用！"), gr.update(
                variant="primary",
                interactive=True,
                value="提交研精验证"
            ), user_state, guest_id_state
            return
        
        # 扣减次数
        user_data["guest_usage"][guest_id]["usage_count"] += 1
        save_user_data(user_data)
    
    # 步骤1：模型初始化
    yield gr.update(value=f"### {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 处理进度\n1. 正在初始化模型，准备研精研判..."), gr.update(
        variant="secondary",
        interactive=False,
        value="正在处理中...（步骤1/4：模型初始化）"
    ), user_state, guest_id_state
    
    # 步骤2：双模型同步答题
    result_queue = queue.Queue()
    threads = [
        threading.Thread(target=call_tongyi_answer, args=(question, result_queue)),
        threading.Thread(target=call_zhipu_answer, args=(question, result_queue))
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=THREAD_TIMEOUT)
    
    yield gr.update(value=f"### {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 处理进度\n2. 双模型正在同步答题，深度分析中..."), gr.update(
        variant="secondary",
        interactive=False,
        value="正在处理中...（步骤2/4：双模型答题）"
    ), user_state, guest_id_state
    
    # 获取答题结果
    tongyi_ans = ""
    zhipu_ans = ""
    while not result_queue.empty():
        key, val = result_queue.get()
        if key == "tongyi_ans":
            tongyi_ans = val
        elif key == "zhipu_ans":
            zhipu_ans = val
    if not tongyi_ans or not zhipu_ans:
        error_msg = f"答题模型调用失败：\n研精千问：{tongyi_ans}\n研精清言：{zhipu_ans}"
        yield gr.update(value=error_msg), gr.update(
            variant="primary",
            interactive=True,
            value="提交研精验证"
        ), user_state, guest_id_state
        return
    
    # 步骤3：双裁判交叉核验
    pure_tongyi_ans = tongyi_ans.replace("研精千问作答：\n", "")
    pure_zhipu_ans = zhipu_ans.replace("研精清言作答：\n", "")
    
    yield gr.update(value=f"### {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 处理进度\n3. 双裁判正在中立研判，交叉验证中..."), gr.update(
        variant="secondary",
        interactive=False,
        value="正在处理中...（步骤3/4：裁判核验）"
    ), user_state, guest_id_state
    
    # 启动裁判线程
    judge_threads = [
        threading.Thread(target=neutral_judge_tongyi, args=(question, pure_tongyi_ans, result_queue, "jt_t")),
        threading.Thread(target=neutral_judge_zhipu, args=(question, pure_tongyi_ans, result_queue, "jt_z")),
        threading.Thread(target=neutral_judge_tongyi, args=(question, pure_zhipu_ans, result_queue, "jz_t")),
        threading.Thread(target=neutral_judge_zhipu, args=(question, pure_zhipu_ans, result_queue, "jz_z"))
    ]
    for t in judge_threads:
        t.start()
    for t in judge_threads:
        t.join(timeout=THREAD_TIMEOUT)
    
    # 获取裁判结果
    jt_t = jt_z = jz_t = jz_z = "研精裁判调用失败"
    while not result_queue.empty():
        key, val = result_queue.get()
        if key == "jt_t":
            jt_t = val
        elif key == "jt_z":
            jt_z = val
        elif key == "jz_t":
            jz_t = val
        elif key == "jz_z":
            jz_z = val
    
    # 步骤4：融合结论生成结果
    yield gr.update(value=f"### {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 处理进度\n4. 正在融合研判结论，生成研精结果..."), gr.update(
        variant="secondary",
        interactive=False,
        value="正在处理中...（步骤4/4：结论融合）"
    ), user_state, guest_id_state
    
    # 融合终审结果（包含直接回答问题功能）
    final_judgment = fuse_consensus(
        question, tongyi_ans, zhipu_ans,
        jt_t, jz_z, jz_t, jz_z
    )
    
    # 组装最终输出
    tongyi_judge_show = jt_t if is_judge_consistent(jt_t, jz_z) else f"{jt_t}\n{jt_z}"
    zhipu_judge_show = jz_t if is_judge_consistent(jz_t, jz_z) else f"{jz_t}\n{jz_z}"
    
    # 游客剩余次数提示
    tip_text = ""
    if user_state.get("is_guest"):
        remain_count = FREE_USE_LIMIT - (user_data["guest_usage"][guest_id]["usage_count"])
        tip_text = f"\n<div style='color: #ff6600; font-size: 12px; margin: 10px 0;'>💡 游客提示：本次使用后剩余免费次数：{remain_count}次</div>"
    
    final_result = f"""# {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} 多模型研精验证结果
## 待解问题：{question}
{final_judgment}{tip_text}

## 📄 原始作答与裁判详情
<div style="font-size: 12px; color: #444; line-height: 1.6; word-wrap: break-word; word-break: break-all;">
### 研精千问作答
{tongyi_ans}

### 研精裁判判定结果
{tongyi_judge_show}

---

### 研精清言作答
{zhipu_ans}

### 研精裁判判定结果
{zhipu_judge_show}
</div>"""
    
    # 最终状态：返回结果+恢复按钮
    yield gr.update(value=final_result), gr.update(
        variant="primary",
        interactive=True,
        value="提交研精验证"
    ), user_state, guest_id_state

# ===================== 10. Web界面（v1.4增强版：新增直接回答功能） =====================
with gr.Blocks(
    title=f"{PLATFORM_NAME_CN} {PLATFORM_NAME_EN} - 多模型研精验证平台（v1.4）",
    theme=gr.themes.Soft(),
    css="""
    /* 基础样式 */
    #platform-title { margin-bottom: 10px; text-align: center; }
    #logo-area { text-align: center; margin-bottom: 10px; }
    #logo { font-size: 40px; line-height: 1; margin-bottom: 5px; }
    
    /* 主布局：左窄栏+右上下布局 */
    #main-row { width: 100% !important; margin: 0 !important; padding: 0 !important; display: flex !important; }
    
    /* 左侧固定面板（280px）- 保留注册/打赏 */
    #left-panel { 
        width: 280px !important;
        max-width: 280px !important;
        min-width: 280px !important;
        padding: 15px; 
        border-right: 1px solid #e0e0e0; 
        height: calc(100vh - 80px) !important; 
        overflow-y: auto;
        flex: none !important;
        display: block !important;
    }
    
    /* 右侧主内容区：上下布局（输入框+结果区） */
    #right-main { 
        padding: 20px; 
        height: calc(100vh - 80px) !important; 
        overflow-y: auto;
        flex: 1 !important;
        width: calc(100% - 280px) !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 20px !important;
    }
    
    /* 输入区域：占顶部空间，宽度100% */
    #input-area { width: 100% !important; flex: none !important; }
    
    /* 答案区域：在输入框正下方，滑动显示，宽度100% */
    #result-area { 
        border: 1px solid #e0e0e0; 
        border-radius: 8px; 
        padding: 20px;
        max-height: 550px !important; 
        overflow-y: auto !important;
        width: 100% !important;
        word-wrap: break-word !important;
        word-break: break-all !important;
        white-space: pre-wrap !important;
        flex: 1 !important;
    }
    
    /* 打赏二维码区域 - 确保显示 */
    #reward-area {
        margin-top: 20px;
        padding: 15px;
        border-radius: 8px;
        background-color: #f9f9f9;
        text-align: center;
        display: block !important;
        visibility: visible !important;
    }
    #reward-qrcode {
        width: 180px !important;
        height: 180px !important;
        margin: 0 auto 10px !important;
        border: 1px solid #eee !important;
        border-radius: 4px !important;
        display: block !important;
    }
    #reward-text {
        font-size: 12px;
        color: #666;
        line-height: 1.5;
    }
    
    /* 技术特点样式 */
    #tech-features {
        background-color: #e8f4f8;
        border-left: 4px solid #4299e1;
        padding: 12px 18px;
        margin: 15px auto;
        border-radius: 6px;
        font-size: 13px;
        color: #333;
        max-width: 90%;
        line-height: 1.8;
    }
    
    /* 免责声明样式 */
    #disclaimer {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 12px 18px;
        margin: 20px auto;
        border-radius: 6px;
        font-size: 13px;
        color: #333;
        max-width: 90%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 底部合并信息样式：同一行显示，居中对齐 */
    #footer-info {
        text-align: center;
        font-size: 12px;
        color: #666;
        margin: 20px 0 30px 0;
        padding-top: 10px;
        border-top: 1px solid #eee;
        line-height: 1.5;
    }
    
    /* 其他样式优化 */
    .gr-button-lg { width: 100%; }
    .custom-textbox { font-size: 14px; width: 100% !important; min-height: 120px !important; }
    .custom-result { font-size: 14px; line-height: 1.8; width: 100% !important; }
    #result-area .gr-markdown {
        width: 100% !important;
        word-wrap: break-word !important;
        word-break: break-all !important;
    }
    .auth-tab { padding: 8px; }
    #left-panel .gr-textbox { margin-bottom: 8px; padding: 6px 10px; }
    #left-panel .gr-button { margin-bottom: 8px; padding: 6px; }
    #left-panel .gr-markdown { font-size: 13px; margin-bottom: 8px; }
    """
) as demo:
    # 状态变量
    user_state = gr.State({"is_login": False, "username": "", "is_guest": False})
    guest_id_state = gr.State("")
    
    # 顶部Logo+标题
    gr.HTML("""
    <div id="logo-area">
        <div id="logo">🫘</div>
    </div>
    """)
    gr.Markdown(f"""# {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN}""", elem_id="platform-title")
    
    # 研精豆技术特点描述
    gr.HTML("""
    <div id="tech-features">
        <strong>🔧 技术特点</strong><br>
        针对单模型易出现的计算偏差、知识点疏漏、逻辑自洽性不足等问题，研精豆独创<strong>多模型分布式研精引擎</strong>，通过端到端的智能研判算法与中立裁判交叉验证机制，实现对答题结果的多层级精准校验；依托动态共识融合技术，突破单模型"单一判断"的局限性，从根源上提升答案的可信度与准确性，为用户提供远超单模型的智能分析体验。
    </div>
    """)
    
    # 主布局Row：左（注册/打赏）+ 右（输入+结果上下布局）
    with gr.Row(elem_id="main-row"):
        # 左侧：注册/登录/打赏面板（保留原功能）
        with gr.Column(elem_id="left-panel"):
            gr.Markdown("#### 🔐 账号管理")
            
            # 登录/注册区域
            with gr.Column(elem_id="auth-area"):
                auth_tabs = gr.Tabs()
                
                with auth_tabs:
                    with gr.TabItem("登录", elem_classes="auth-tab"):
                        login_msg = gr.Markdown("登录后无次数限制")
                        login_username = gr.Textbox(label="用户名", placeholder="请输入用户名")
                        login_password = gr.Textbox(label="密码", type="password", placeholder="请输入密码")
                        login_btn = gr.Button("登录", variant="primary")
                        guest_btn = gr.Button("游客模式（3次）", variant="secondary")
                    
                    with gr.TabItem("注册", elem_classes="auth-tab"):
                        reg_msg = gr.Markdown("注册新账号")
                        reg_username = gr.Textbox(label="用户名", placeholder="设置用户名")
                        reg_password = gr.Textbox(label="密码", type="password", placeholder="≥6位")
                        reg_confirm_pwd = gr.Textbox(label="确认密码", type="password", placeholder="再次输入")
                        reg_btn = gr.Button("注册", variant="primary")
                
                # 登录状态显示
                login_status = gr.Markdown("🔒 未登录")
                logout_btn = gr.Button("退出登录", variant="stop", visible=False)
            
            # 打赏二维码区域（强制显示）
            with gr.Column(elem_id="reward-area"):
                gr.Markdown("#### 🎁 请作者喝杯咖啡")
                gr.HTML("""
                <img id="reward-qrcode" 
                     src="https://drive-h.quark.cn/1/clouddrive/file/thumbnail?fid=55f7300b727d49399662fbd89fa4443a&pr=ucpro&fr=pc" />
                """)
                gr.Markdown("""
                <div id="reward-text">
                token太贵，觉得好用请自由打赏～<br>
                你的支持是持续更新的动力 💪
                </div>
                """)
        
        # 右侧：主功能区（上下布局：输入框 + 结果区）
        with gr.Column(elem_id="right-main"):
            # 输入区域（顶部）
            with gr.Column(elem_id="input-area"):
                question = gr.Textbox(
                    label="请输入需要研精验证的问题",
                    lines=4,
                    placeholder="示例1：某电商商品原价3200元，8.5折后减300，再缴3%增值税，最终支付多少？\n示例2：请辨析不当得利和无因管理的核心区别（符合《民法典》）\n示例3：甲/乙/丙仓库对应A/B/C货物，推理各仓库存放类型（甲≠A，乙≠B，丙≠C）",
                    elem_classes=["custom-textbox"]
                )
                submit_btn = gr.Button("提交研精验证", variant="primary", size="lg", interactive=False)
            
            # 结果区域（输入框正下方，滑动显示）
            with gr.Column(elem_id="result-area"):
                result = gr.Markdown(
                    label=f"{PLATFORM_NAME_CN} 验证结果", 
                    value=f"等待登录后提交问题，{PLATFORM_NAME_CN}为你提供双模型深度研精验证+直接答案回应！",
                    elem_classes=["custom-result"]
                )
    
    # 免责声明
    gr.HTML("""
    <div id="disclaimer">
        <strong>📢 免责声明</strong><br>
        1. 本工具为AI辅助研精验证工具，所有结果仅供学习研究参考，不构成任何决策依据；<br>
        2. 请遵守相关法律法规，严禁用于违法违规、商业牟利等非授权场景；<br>
        3. 游客模式提供3次免费使用机会，注册账号后无次数限制；<br>
        4. 平台仅提供技术服务，API调用费用由用户自行承担。
    </div>
    """)
    
    # 底部合并信息
    gr.HTML(f"""
    <div id="footer-info">
        📞 联系方式：13916379825@139.com | 研精豆多模型研精验证平台 v{CURRENT_VERSION} | 通过 API 使用 | 使用 Gradio 构建 | 设置
    </div>
    """)
    
    # ===================== 交互逻辑 =====================
    # 注册按钮逻辑
    reg_btn.click(
        fn=user_register,
        inputs=[reg_username, reg_password, reg_confirm_pwd],
        outputs=[reg_msg, reg_password, reg_confirm_pwd]
    )
    
    # 登录按钮逻辑
    login_btn.click(
        fn=user_login,
        inputs=[login_username, login_password, user_state, guest_id_state],
        outputs=[login_msg, user_state, guest_id_state]
    ).then(
        fn=lambda us: (
            gr.update(interactive=True),
            gr.update(value=f"✅ 已登录：{us['username']}"),
            gr.update(visible=True)
        ),
        inputs=[user_state],
        outputs=[submit_btn, login_status, logout_btn]
    )
    
    # 游客模式逻辑
    guest_btn.click(
        fn=guest_mode,
        inputs=[user_state, guest_id_state],
        outputs=[login_msg, user_state, guest_id_state]
    ).then(
        fn=lambda us: (
            gr.update(interactive=True),
            gr.update(value=f"✅ {us['username']} | 剩余{FREE_USE_LIMIT - load_user_data()['guest_usage'][us['username'].replace('游客','')]['usage_count']}次"),
            gr.update(visible=True)
        ),
        inputs=[user_state],
        outputs=[submit_btn, login_status, logout_btn]
    )
    
    # 退出登录逻辑
    logout_btn.click(
        fn=logout,
        inputs=[user_state, guest_id_state],
        outputs=[login_status, user_state, guest_id_state]
    ).then(
        fn=lambda: (
            gr.update(interactive=False),
            gr.update(visible=False),
            gr.update(value="🔒 未登录"),
            gr.update(value="等待登录后提交问题，研精豆为你提供双模型深度研精验证+直接答案回应！")
        ),
        outputs=[submit_btn, logout_btn, login_msg, result]
    )
    
    # 提交验证逻辑
    submit_btn.click(
        fn=core_verify_logic,
        inputs=[question, user_state, guest_id_state],
        outputs=[result, submit_btn, user_state, guest_id_state],
        show_progress=False
    )

# ===================== 程序启动 =====================
if __name__ == "__main__":
    init_user_data()
    print(f"\n🚀 {PLATFORM_NAME_CN} | {PLATFORM_NAME_EN} v{CURRENT_VERSION} 启动成功！")
    print(f"🌐 访问地址：http://localhost:7860 | 外网访问：http://你的服务器IP:7860")
    print(f"⚙️  核心能力：多模型深度研精+双裁判中立研判+直接回应问题+用户注册+游客次数限制")
    print(f"📌 版本特性：新增问题直接回答+文案精简+底部信息合并+结论前缀简化+技术特点描述+答案显示在问题下方\n")
    
    demo.launch(
        server_port=7860,
        server_name="0.0.0.0",
        show_error=True,
        debug=False,
        share=False,
        auth=None
    )
