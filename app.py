import os
import datetime
import threading
import tiktoken
from flask import Flask, render_template, request, jsonify, session
from utils.link_wppTool import run_wpp_and_check
from utils.filter import read_log_file, extract_enabled_keywords_from_filter_file, extract_exclude_keywords_from_filter_file, filter_log_by_keywords
from utils.parse_log import preprocess_log_for_llm, group_similar_logs, save_file
from utils.llm_expertgpt import LLM_helper
from utils.llm_ollama import OllamaLLM_helper, get_available_ollama_models
from configs.key import expertgpt_token
import markdown
import uuid
import importlib
import time

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "log_data")
app.secret_key = 'test_2025'

project_root = os.path.dirname(os.path.abspath(__file__))

user_progress = {}
user_results = {}
user_last_activity = {}

last_cleanup_time = 0

def get_session_id():
    """獲取或建立 session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


"""# 全域變數儲存進度狀態和結果
progress_status = {
    'percentage': 0,
    'message': 'Ready',
    'status': 'idle'
}

analysis_result = {
    'llm_result_html': None,
    'log_output_path': None
}"""

def update_progress(percentage, message, session_id):
    """更新特定使用者的進度狀態"""
    if session_id not in user_progress:
        user_progress[session_id] = {}
    
    user_progress[session_id]['percentage'] = percentage
    user_progress[session_id]['message'] = message
    user_progress[session_id]['status'] = 'processing' if percentage < 100 else 'completed'
    print(f"Progress [{session_id[:8]}]: {percentage}% - {message}")

"""def update_progress(percentage, message):

    global progress_status
    progress_status['percentage'] = percentage
    progress_status['message'] = message
    progress_status['status'] = 'processing' if percentage < 100 else 'completed'
    print(f"Progress: {percentage}% - {message}")"""

@app.route("/progress")
def get_progress():
    """回傳目前進度狀態"""
    session_id = get_session_id()
    return jsonify(user_progress.get(session_id, {
        'percentage': 0,
        'message': 'Ready',
        'status': 'idle'
    }))

@app.route("/result")
def get_result():
    """回傳分析結果"""

    session_id = get_session_id()
    result = user_results.get(session_id, {
        'llm_result_html': None,
        'log_output_path': None,
        'token_info': None
    })
    
    filter_dir = rf"{project_root}\filter"
    available_filters = []
    if os.path.exists(filter_dir):
        available_filters = [f for f in os.listdir(filter_dir) if f.endswith('.tat')]
    
    return render_template("index.html", 
                         llm_result_html=result['llm_result_html'],
                         log_output_path=result['log_output_path'],
                         token_info=result.get('token_info'),
                         available_filters=available_filters)

def process_analysis_async(filter_path, etl_path, output_dir, llm_helper, prompt, session_id, exclude_keywords=None):
    """非同步處理分析任務"""
    global user_progress, user_results
    
    try:
        user_results[session_id]['status'] = 'processing'
        #print("etl_path:", etl_path)
        # 步驟 1: 執行 WPP 工具
        update_progress(30, "[Sandbox] Skip Running WPP tool...", session_id)
        #run_wpp_and_check(etl_path)
        
        # 步驟 2: 讀取日誌檔案
        update_progress(35, "Reading log file...", session_id)
        #log_file = f"{etl_path}.log"
        log_lines = read_log_file(etl_path)
        
        # 步驟 3: 提取過濾關鍵字
        update_progress(40, "Extracting filter keywords...", session_id)
        filter_keywords = extract_enabled_keywords_from_filter_file(filter_path)
        tat_exclude_keywords = extract_exclude_keywords_from_filter_file(filter_path)
        merged_exclude = tat_exclude_keywords + exclude_keywords  # tat entries are dicts, manual entries are plain strings
        
        # 步驟 4: 過濾日誌
        update_progress(55, "Filtering log entries...", session_id)
        filtered_log = filter_log_by_keywords(log_lines, filter_keywords, exclude_keywords=merged_exclude)
        save_file(os.path.join(output_dir, "filtered.log"), filtered_log)
        
        # 步驟 5: 預處理日誌
        update_progress(70, "Preprocessing log for LLM...", session_id)
        processed_lines = preprocess_log_for_llm(filtered_log)
        # grouped = group_similar_logs(processed_lines)
        grouped = processed_lines
        
        save_filtered_log_path = os.path.join(output_dir, "filtered_preprocessed.log")
        save_file(save_filtered_log_path, grouped)
        
        # 步驟 6: LLM 分析
        update_progress(85, "Running LLM analysis...", session_id)
        llm_result, token_info = llm_helper.analyze_log_sandbox(
            system_content=prompt,
            log=str(grouped)
        )
        
        # 步驟 7: 完成
        update_progress(100, "Analysis completed!", session_id)

        if session_id not in user_results:
            user_results[session_id] = {}
        
        # 儲存結果到全域變數
        user_results[session_id]['llm_result_html'] = markdown.markdown(llm_result if isinstance(llm_result, str) else str(llm_result), extensions=["fenced_code", "tables"])
        user_results[session_id]['log_output_path'] = save_filtered_log_path
        user_results[session_id]['token_info'] = token_info
        
        user_progress[session_id]['status'] = 'completed'
        
    except Exception as e:
        update_progress(0, f"Error: {str(e)}", session_id)
        user_progress[session_id]['status'] = 'error'

def has_sys_prompt_variable(file_path):
    """動態載入模組並檢查 SYS_PROMPT 變數是否存在且為字串"""
    try:

        if hasattr(file_path, 'read'):
            content = file_path.read().decode('utf-8')
            file_path.seek(0)
            return 'SYS_PROMPT' in content and 'SYS_PROMPT =' in content
        # 動態載入模組
        spec = importlib.util.spec_from_file_location("temp_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 檢查是否有 SYS_PROMPT 屬性且為字串
        if hasattr(module, 'SYS_PROMPT'):
            sys_prompt = getattr(module, 'SYS_PROMPT')
            if isinstance(sys_prompt, str) and len(sys_prompt.strip()) > 0:
                return True
        
        return False
        
    except Exception as e:
        print(f"Error loading module {file_path}: {e}")
        return False

def check_valid_prompt_dir(prompt_dir):
    available_prompts = []
    if os.path.exists(prompt_dir):
        prompts_path = [f for f in os.listdir(prompt_dir) if f.endswith('.py')]
        for prompt_file in prompts_path:
            prompt_file_path = os.path.join(prompt_dir, prompt_file)
            if has_sys_prompt_variable(prompt_file_path):
                available_prompts.append(prompt_file)
    print("available_prompts:", available_prompts)
    return available_prompts

@app.route("/", methods=["GET", "POST"])
def index():
    global user_progress, user_results

    ### session set up 
    session_id = get_session_id()
    update_user_activity(session_id)
    if session_id not in user_progress:
        user_progress[session_id] = {'percentage': 0, 'message': 'Starting...', 'status': 'processing'}
    if session_id not in user_results:
        user_results[session_id] = {'llm_result_html': None, 'log_output_path': None, 'token_info': None}
    cleanup_old_sessions()
    ### 
    
    filter_dir = rf"{project_root}\filter"
    available_filters = []
    if os.path.exists(filter_dir):
        available_filters = [f for f in os.listdir(filter_dir) if f.endswith('.tat')]
    print("available_filters:", available_filters)


    prompt_dir = rf"{project_root}\prompt"
    custom_prompt_dir = rf"{project_root}\custom_prompt"

    available_prompts = check_valid_prompt_dir(prompt_dir)
    available_custom_prompts = check_valid_prompt_dir(custom_prompt_dir)

    

    
    if request.method == "POST":
        # 重置進度狀態和結果
        user_progress[session_id] = {'percentage': 0, 'message': 'Starting...', 'status': 'processing'}
        user_results[session_id] = {'llm_result_html': None, 'log_output_path': None, 'token_info': None}

        llm_backend = request.form.get("llm_backend", "expertgpt")
        ollama_model = request.form.get("ollama_model", "llama3.1:8b")
        ollama_num_ctx = int(request.form.get("ollama_num_ctx", 32768))

        if llm_backend == "ollama":
            llm_helper = OllamaLLM_helper()
            llm_helper.set_up(model=ollama_model, num_ctx=ollama_num_ctx)
        else:
            llm_helper = LLM_helper()
            llm_helper.set_up(expertgpt_token=expertgpt_token)
        
        # === 準備上傳資料夾 ===
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # === 儲存上傳的檔案 ===
        selected_filter = request.form.get("filter_file") 
        custom_prompt_content = request.form.get("prompt_content")
        exclude_keywords_raw = request.form.get("exclude_keywords", "")
        exclude_keywords = [k.strip() for k in exclude_keywords_raw.split(",") if k.strip()]
        #selected_prompt = request.form.get("prompt_file") 
        etl_file = request.files.get("etl_file")

        if selected_filter:
            filter_path = os.path.join(filter_dir, selected_filter)
        #if selected_prompt:
        #    prompt_path = os.path.join(prompt_dir, selected_prompt)

        if not etl_file:
            return render_template("index.html", 
                                 llm_result_html="Please upload .log file.",
                                 available_filters=available_filters,
                                 available_prompts=available_prompts,
                                 available_custom_prompts=available_custom_prompts)
        
        if not custom_prompt_content or not filter_path:
            return render_template("index.html", 
                                 llm_result_html="Please select both filter and prompt.",
                                 available_filters=available_filters,
                                 available_prompts=available_prompts,
                                 available_custom_prompts=available_custom_prompts)


        output_dir = os.path.join(project_root, rf"log_data\run_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        etl_path = os.path.join(output_dir, etl_file.filename)
        etl_file.save(etl_path)

        # 啟動非同步處理
        thread = threading.Thread(
            target=process_analysis_async, 
            args=(filter_path, etl_path, output_dir, llm_helper, custom_prompt_content, session_id, exclude_keywords)
        )
        thread.daemon = True
        thread.start()
        
        # 回傳空的回應，讓前端開始輪詢
        return '', 200

    return render_template("index.html", 
                         llm_result_html=user_results[session_id]['llm_result_html'], 
                         log_output_path=user_results[session_id]['log_output_path'],
                         token_info=user_results[session_id].get('token_info'),
                         available_filters=available_filters,
                         available_prompts=available_prompts,
                         available_custom_prompts=available_custom_prompts)



@app.route("/upload_prompt", methods=["POST"])
def upload_prompt():
    if 'prompt_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['prompt_file']

    print(file, type(file))
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not has_sys_prompt_variable(file):
        return jsonify({'success': False, 'message': 'Please select a .py file'})
    try:
        custom_prompt_dir = rf"{project_root}\custom_prompt"
        file_path = os.path.join(custom_prompt_dir, file.filename)

        
        if os.path.exists(file_path):
            return jsonify({'success': False, 'message': f'File "{file.filename}" already exists'})
        
        file.save(file_path)
        
        return jsonify({'success': True, 'message': f'Prompt "{file.filename}" uploaded successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error uploading file: {str(e)}'})

@app.route("/get_prompt", methods=["GET"])
def get_prompt():
    custom_prompt_dir = rf"{project_root}\custom_prompt"
    available_custom_prompts = check_valid_prompt_dir(custom_prompt_dir)
    
    return jsonify({'prompts': available_custom_prompts})


@app.route("/upload_filter", methods=["POST"])
def upload_filter():
    """上傳新的 filter 檔案"""
    if 'filter_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['filter_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    # 檢查檔案副檔名
    if not file.filename.lower().endswith('.tat'):
        return jsonify({'success': False, 'message': 'Please select a .tat file'})
    
    try:
        filter_dir = rf"{project_root}\filter"
        # 儲存檔案
        file_path = os.path.join(filter_dir, file.filename)
        
        # 檢查檔案是否已存在
        if os.path.exists(file_path):
            return jsonify({'success': False, 'message': f'File "{file.filename}" already exists'})
        
        file.save(file_path)
        
        return jsonify({'success': True, 'message': f'Filter "{file.filename}" uploaded successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error uploading file: {str(e)}'})

@app.route("/get_filters", methods=["GET"])
def get_filters():
    """獲取最新的 filter 列表"""
    filter_dir = rf"{project_root}\filter"
    available_filters = []
    if os.path.exists(filter_dir):
        available_filters = [f for f in os.listdir(filter_dir) if f.endswith('.tat')]
    
    return jsonify({'filters': available_filters})


@app.route("/estimate_tokens", methods=["POST"])
def estimate_tokens():
    """Estimate token count of filtered log without calling LLM."""
    try:
        filter_name = request.form.get("filter_file", "")
        etl_file = request.files.get("etl_file")
        exclude_keywords_raw = request.form.get("exclude_keywords", "")
        estimate_exclude_keywords = [k.strip() for k in exclude_keywords_raw.split(",") if k.strip()]

        if not filter_name or not etl_file:
            return jsonify({"error": "filter_file and etl_file are required"}), 400

        filter_dir = rf"{project_root}\filter"
        filter_path = os.path.join(filter_dir, filter_name)
        if not os.path.exists(filter_path):
            return jsonify({"error": f"Filter not found: {filter_name}"}), 404

        # Run the same pipeline as the main analysis
        import tempfile, shutil
        tmp_dir = tempfile.mkdtemp()
        try:
            tmp_log_path = os.path.join(tmp_dir, etl_file.filename)
            etl_file.save(tmp_log_path)

            log_lines = read_log_file(tmp_log_path)
            filter_keywords = extract_enabled_keywords_from_filter_file(filter_path)
            tat_exclude_keywords = extract_exclude_keywords_from_filter_file(filter_path)
            merged_exclude = tat_exclude_keywords + estimate_exclude_keywords  # tat entries are dicts, manual entries are plain strings
            filtered_log = filter_log_by_keywords(log_lines, filter_keywords, exclude_keywords=merged_exclude)
            processed_lines = preprocess_log_for_llm(filtered_log)
            # grouped = group_similar_logs(processed_lines)
            grouped = processed_lines
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        log_text = str(grouped)
        enc = tiktoken.get_encoding("cl100k_base")
        token_count = len(enc.encode(log_text))
        filtered_line_count = len(filtered_log) if isinstance(filtered_log, list) else log_text.count("\n")

        return jsonify({
            "estimated_tokens": token_count,
            "filtered_lines": filtered_line_count
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_ollama_models", methods=["GET"])
def get_ollama_models():
    """回傳目前 Ollama 可用的模型列表"""
    models = get_available_ollama_models()
    return jsonify({'models': models})


def get_sys_prompt_content(file_path):
    """獲取檔案中的 SYS_PROMPT 內容"""
    try:
        spec = importlib.util.spec_from_file_location("temp_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'SYS_PROMPT'):
            return getattr(module, 'SYS_PROMPT')
        return ""
    except Exception as e:
        print(f"Error loading prompt content from {file_path}: {e}")
        return ""

@app.route("/load_prompt", methods=["POST"])
def load_prompt():
    """載入 prompt 內容"""
    data = request.get_json()
    prompt_type = data.get('type')  # 'template' or 'custom'
    prompt_file = data.get('file')
    
    if prompt_type == 'template':
        prompt_dir = rf"{project_root}\prompt"
    else:
        prompt_dir = rf"{project_root}\custom_prompt"
    
    file_path = os.path.join(prompt_dir, prompt_file)
    content = get_sys_prompt_content(file_path)
    
    return jsonify({'content': content})

@app.route("/update_prompt", methods=["POST"])
def update_prompt():
    """更新現有的自訂 prompt"""
    data = request.get_json()
    filename = data.get('filename')
    content = data.get('content')
    
    if not filename or not content:
        return jsonify({'success': False, 'message': 'Filename and content are required'})
    
    custom_dir = rf"{project_root}\custom_prompt"
    file_path = os.path.join(custom_dir, filename)
    
    # 檢查檔案是否存在
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'File does not exist'})
    
    try:
        # 直接覆蓋現有檔案
        file_content = f'''SYS_PROMPT = """{content}"""
'''
        with open(file_path, 'w', encoding='utf-8', errors="replace") as f:
            f.write(file_content)
        
        return jsonify({'success': True, 'message': f'Prompt updated: {filename}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating file: {str(e)}'})

@app.route("/save_prompt", methods=["POST"])
def save_prompt():
    """儲存自訂 prompt"""
    data = request.get_json()
    filename = data.get('filename')
    content = data.get('content')
    
    if not filename or not content:
        return jsonify({'success': False, 'message': 'Filename and content are required'})
    
    # 確保檔名以 .py 結尾
    if not filename.endswith('.py'):
        filename += '.py'
    
    custom_dir = rf"{project_root}\custom_prompt"
    os.makedirs(custom_dir, exist_ok=True)
    
    file_path = os.path.join(custom_dir, filename)
    
    try:
        # 建立完整的 Python 檔案內容
        file_content = f'''SYS_PROMPT = """{content}"""
        '''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        return jsonify({'success': True, 'message': f'Prompt saved as {filename}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving file: {str(e)}'})

def update_user_activity(session_id):
    global user_last_activity
    user_last_activity[session_id] = time.time()

def cleanup_old_sessions():
    """清理超過 1 小時的舊 session"""
    global last_cleanup_time, user_last_activity
    current_time = time.time()
    if current_time - last_cleanup_time < 1200:
        return
    sessions_to_remove = []
    
    for session_id in list(user_progress.keys()):
        # 假設 session 有最後活動時間
        if session_id in user_last_activity:
            if current_time - user_last_activity[session_id] > 3600:  # 1小時
                sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        user_progress.pop(session_id, None)
        user_results.pop(session_id, None)
        user_last_activity.pop(session_id, None)
        print(f"Cleaned up session: {session_id[:8]}")
    last_cleanup_time = current_time

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=57777)