import os
import datetime
import threading
import json
from flask import Flask, render_template, request, jsonify
from utils.link_wppTool import run_wpp_and_check
from utils.filter import read_log_file, extract_enabled_keywords_from_filter_file, filter_log_by_keywords
from utils.parse_log import preprocess_log_for_llm, group_similar_logs, save_file
from utils.llm_expertgpt import LLM_helper
from configs.key import expertgpt_token
import markdown
import importlib

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "log_data")

project_root = os.path.dirname(os.path.abspath(__file__))

# 全域變數儲存進度狀態和結果
progress_status = {
    'percentage': 0,
    'message': 'Ready',
    'status': 'idle'
}

analysis_result = {
    'llm_result_html': None,
    'log_output_path': None
}

def update_progress(percentage, message):
    """更新進度狀態"""
    global progress_status
    progress_status['percentage'] = percentage
    progress_status['message'] = message
    progress_status['status'] = 'processing' if percentage < 100 else 'completed'
    print(f"Progress: {percentage}% - {message}")

@app.route("/progress")
def get_progress():
    """回傳目前進度狀態"""
    return jsonify(progress_status)

@app.route("/result")
def get_result():
    """回傳分析結果"""
    filter_dir = rf"{project_root}\filter"
    available_filters = []
    if os.path.exists(filter_dir):
        available_filters = [f for f in os.listdir(filter_dir) if f.endswith('.tat')]
    
    return render_template("index.html", 
                         llm_result_html=analysis_result['llm_result_html'],
                         log_output_path=analysis_result['log_output_path'],
                         available_filters=available_filters)

def process_analysis_async(filter_path, etl_path, output_dir, llm_helper, prompt):
    """非同步處理分析任務"""
    global progress_status, analysis_result
    
    try:
        progress_status['status'] = 'processing'
        #print("etl_path:", etl_path)
        # 步驟 1: 執行 WPP 工具
        update_progress(30, "[Sandbox] Skip Running WPP tool...")
        #run_wpp_and_check(etl_path)
        
        # 步驟 2: 讀取日誌檔案
        update_progress(35, "Reading log file...")
        #log_file = f"{etl_path}.log"
        log_lines = read_log_file(etl_path)
        
        # 步驟 3: 提取過濾關鍵字
        update_progress(40, "Extracting filter keywords...")
        filter_keywords = extract_enabled_keywords_from_filter_file(filter_path)
        
        # 步驟 4: 過濾日誌
        update_progress(55, "Filtering log entries...")
        filtered_log = filter_log_by_keywords(log_lines, filter_keywords)
        save_file(os.path.join(output_dir, "filtered.log"), filtered_log)
        
        # 步驟 5: 預處理日誌
        update_progress(70, "Preprocessing log for LLM...")
        processed_lines = preprocess_log_for_llm(filtered_log)
        grouped = group_similar_logs(processed_lines)
        
        save_filtered_log_path = os.path.join(output_dir, "filtered_preprocessed.log")
        save_file(save_filtered_log_path, grouped)
        
        # 步驟 6: LLM 分析
        update_progress(85, "Running LLM analysis...")
        llm_result = llm_helper.analyze_log_sandbox(
            system_content=prompt,
            log=str(grouped)
        )
        
        # 步驟 7: 完成
        update_progress(100, "Analysis completed!")
        
        # 儲存結果到全域變數
        analysis_result['llm_result_html'] = markdown.markdown(llm_result, extensions=["fenced_code", "tables"])
        analysis_result['log_output_path'] = save_filtered_log_path
        
        progress_status['status'] = 'completed'
        
    except Exception as e:
        update_progress(0, f"Error: {str(e)}")
        progress_status['status'] = 'error'

def has_sys_prompt_variable(file_path):
    """動態載入模組並檢查 SYS_PROMPT 變數是否存在且為字串"""
    try:
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
    global progress_status, analysis_result
    
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
        progress_status = {'percentage': 0, 'message': 'Starting...', 'status': 'processing'}
        analysis_result = {'llm_result_html': None, 'log_output_path': None}
        
        llm_helper = LLM_helper()
        llm_helper.set_up(expertgpt_token=expertgpt_token)
        
        # === 準備上傳資料夾 ===
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # === 儲存上傳的檔案 ===
        selected_filter = request.form.get("filter_file") 
        custom_prompt_content = request.form.get("prompt_content")
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
            args=(filter_path, etl_path, output_dir, llm_helper, custom_prompt_content)
        )
        thread.daemon = True
        thread.start()
        
        # 回傳空的回應，讓前端開始輪詢
        return '', 200

    return render_template("index.html", 
                         llm_result_html=analysis_result['llm_result_html'], 
                         log_output_path=analysis_result['log_output_path'], 
                         available_filters=available_filters,
                         available_prompts=available_prompts,
                         available_custom_prompts=available_custom_prompts)


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
        with open(file_path, 'w', encoding='utf-8') as f:
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=57777)