"""
学情与教学评价智能分析系统 - 主应用（用户隔离版）
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import uuid
import os

# 必须先设置用户，再导入database
# 使用session_state存储用户ID
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# 登录页面
def login_page():
    st.set_page_config(page_title="登录 - 智学链", page_icon="🔐", layout="centered")
    
    # 初始化全局数据库（用于用户账户）
    from database import set_current_user, register_user, authenticate_user, user_exists
    # 使用固定的系统数据库存储用户账户
    set_current_user("system")
    
    st.markdown("""
    <div style="text-align:center;padding:50px 20px;">
        <div style="font-size:5rem;margin-bottom:20px;">📊</div>
        <h1 style="color:#667eea;">智学链</h1>
        <p style="color:#666;font-size:1.1rem;">学情与教学评价智能分析系统</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 登录/注册切换
    tab1, tab2 = st.tabs(["🔓 登录", "📝 注册"])
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with tab1:
            username = st.text_input("👤 用户名", placeholder="请输入您的用户名")
            password = st.text_input("🔑 密码", placeholder="请输入密码", type="password")
            
            if st.button("🔓 登录", use_container_width=True, type="primary"):
                if username.strip() and password.strip():
                    # 验证用户
                    if authenticate_user(username.strip(), password.strip()):
                        # 使用用户名生成固定用户ID
                        user_id = hash(username.strip()) % 10000000
                        st.session_state.user_id = str(user_id)
                        st.session_state.username = username.strip()
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
                else:
                    st.error("请输入用户名和密码")
        
        with tab2:
            new_username = st.text_input("👤 新用户名", placeholder="请输入用户名")
            new_password = st.text_input("🔑 新密码", placeholder="请输入密码", type="password")
            confirm_password = st.text_input("🔑 确认密码", placeholder="请再次输入密码", type="password")
            
            if st.button("📝 注册", use_container_width=True, type="primary"):
                if new_username.strip() and new_password.strip():
                    if new_password == confirm_password:
                        if register_user(new_username.strip(), new_password.strip()):
                            st.success("注册成功！请登录")
                        else:
                            st.error("用户名已存在")
                    else:
                        st.error("两次输入的密码不一致")
                else:
                    st.error("请填写用户名和密码")
        
        st.markdown("""
        <div style="text-align:center;color:#999;font-size:0.9rem;margin-top:20px;">
            <p>💡 提示：每个用户拥有独立的数据空间</p>
            <p>不同用户的数据互不干扰</p>
        </div>
        """, unsafe_allow_html=True)

# 主应用
def main_app():
    # 设置用户数据库
    from database import set_current_user, get_custom_subjects, save_custom_subject, delete_custom_subject
    from database import (
        import_students, save_evaluation, 
        get_student_evaluations, get_class_evaluations,
        save_template, get_templates, get_template, delete_template,
        save_learning_status, save_phase_evaluation,
        save_class, get_classes, delete_class, get_students_by_class
    )
    from analytics import LearningAnalytics
    from visualizations import LearningVisualizer
    from reports import ReportGenerator
    from config import PRESET_SUBJECTS, SCORE_LEVELS
    
    # 初始化当前用户数据库
    set_current_user(st.session_state.user_id)
    
    # 页面配置
    st.set_page_config(
        page_title="学情与教学评价智能分析系统",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS样式（保持不变，略）
    st.markdown("""
    <style>
        /* ... 原有CSS样式 ... */
        .user-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            text-align: center;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化
    analytics = LearningAnalytics()
    viz = LearningVisualizer()
    reporter = ReportGenerator()
    
    # 侧边栏
    with st.sidebar:
        # 用户信息
        st.markdown(f"""
        <div class="user-badge">
            👤 {st.session_state.username}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
        
        st.markdown("---")
        st.markdown('<div class="sidebar-title">📚 智能学情分析系统</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # 科目选择 - 支持自定义
        st.markdown("### 🎯 科目设置")
        
        # 获取自定义科目
        custom_subjects = get_custom_subjects()
        all_subjects = PRESET_SUBJECTS + custom_subjects
        
        # 初始化session_state
        if 'selected_subject' not in st.session_state:
            st.session_state.selected_subject = PRESET_SUBJECTS[0]
        
        # 设置默认选择的索引
        default_subject_index = all_subjects.index(st.session_state.selected_subject) if st.session_state.selected_subject in all_subjects else 0
        
        # 科目选择
        subject_option = st.selectbox(
            "选择科目",
            all_subjects + ["➕ 添加自定义科目..."],
            index=default_subject_index
        )
        
        # 处理自定义科目
        if subject_option == "➕ 添加自定义科目...":
            new_subject = st.text_input("输入科目名称", placeholder="例如：人工智能基础")
            if new_subject and new_subject.strip():
                if st.button("✅ 确认添加", use_container_width=True):
                    if save_custom_subject(new_subject.strip()):
                        st.success(f"✅ 已添加科目：{new_subject}")
                        st.session_state.selected_subject = new_subject.strip()
                        st.rerun()
                    else:
                        st.info("该科目已存在")
                subject = new_subject.strip() if new_subject.strip() else st.session_state.selected_subject
            else:
                subject = st.session_state.selected_subject
        else:
            subject = subject_option
            # 保存选择到session_state
            st.session_state.selected_subject = subject_option
        
        # 显示当前科目
        st.markdown(f"""
        <div style="background:#e3f2fd;border-radius:10px;padding:10px;margin:10px 0;text-align:center;">
            <span style="color:#1976d2;font-weight:600;">当前：{subject}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 管理自定义科目
        if custom_subjects:
            with st.expander("🗑️ 管理自定义科目"):
                del_subject = st.selectbox("选择要删除的科目", custom_subjects)
                if st.button("删除", key="del_sub"):
                    delete_custom_subject(del_subject)
                    st.success(f"已删除：{del_subject}")
                    st.rerun()
        
        st.markdown("---")
        
        # 班级管理
        st.markdown("### 🏫 班级管理")
        
        # 获取班级列表
        classes_df = get_classes(subject=subject)
        class_options = ["➕ 创建新班级..."]
        if not classes_df.empty:
            class_options += [f"{row['class_name']} (ID:{row['class_id']})" for _, row in classes_df.iterrows()]
        
        selected_class = st.selectbox("选择班级", class_options, index=0)
        
        # 创建新班级
        if selected_class == "➕ 创建新班级...":
            new_class_name = st.text_input("班级名称", placeholder="例如：高一(1)班")
            if new_class_name and new_class_name.strip():
                if st.button("✅ 创建班级", use_container_width=True):
                    success, class_id = save_class(new_class_name.strip(), subject)
                    if success:
                        st.success(f"✅ 已创建班级：{new_class_name}")
                        st.rerun()
                    else:
                        st.info("该班级已存在")
            current_class_id = None
            current_class_name = None
        else:
            # 解析选中的班级ID和名称
            current_class_id = int(selected_class.split("ID:")[1][:-1])
            current_class_name = selected_class.split(" (")[0]
        
        # 显示当前班级
        if current_class_name:
            st.markdown(f"""
            <div style="background:#ffe0b2;border-radius:10px;padding:10px;margin:10px 0;text-align:center;">
                <span style="color:#e65100;font-weight:600;">当前班级：{current_class_name}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 管理班级
        if not classes_df.empty:
            with st.expander("🗑️ 管理班级"):
                del_class_name = st.selectbox("选择要删除的班级", 
                                            [f"{row['class_name']} (ID:{row['class_id']})" for _, row in classes_df.iterrows()])
                del_class_id = int(del_class_name.split("ID:")[1][:-1])
                if st.button("删除班级", key="del_class"):
                    delete_class(del_class_id)
                    st.success(f"已删除班级")
                    st.rerun()
        
        # 保存当前班级到session_state
        st.session_state['current_class_id'] = current_class_id
        st.session_state['current_class_name'] = current_class_name
        
        st.markdown("---")
        
        # 功能导航
        st.markdown("### 🧭 功能导航")
        page = st.radio(
            "",
            ["🏠 首页概览", "📐 评价模板", "👥 学生管理", "📝 课后评价", 
             "📈 学情追踪", "📊 数据分析", "📋 阶段总评", "🤖 AI教学策略"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top:0;color:#00bcd4;">✨ 系统特点</h4>
            <ul style="margin-bottom:0;padding-left:20px;">
                <li>课后评价→课前学情</li>
                <li>连续追踪学生成长</li>
                <li>支持任意科目自定义</li>
                <li>AI智能分析辅助</li>
                <li>数据可视化呈现</li>
                <li>多用户数据隔离</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<div class="custom-footer">© 2026 智学链<br>基于国产大模型技术</div>', unsafe_allow_html=True)
    
    # ==================== 以下为原有页面代码，subject变量已更新 ====================
    
    def get_dimension_cols(df):
        exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                       'subject', 'template_id', 'eval_date', 'evaluator', 
                       'total_score', 'comments', 'created_at', 'name']
        # 先过滤掉排除列，再只保留数值类型的列
        filtered_cols = [c for c in df.columns if c not in exclude_cols]
        return df[filtered_cols].select_dtypes(include=['number']).columns.tolist()
    
    def render_metric_card(title, value, delta=None, icon="📊"):
        delta_html = f'<p style="font-size:1rem;color:{"#4caf50" if delta and "+" in str(delta) else "#f44336" if delta else "#666"};margin:0;">{delta}</p>' if delta else ''
        st.markdown(f"""
        <div class="metric-card">
            <p style="font-size:0.9rem;color:#666;margin:0;">{icon} {title}</p>
            <h2 style="font-size:2rem;font-weight:700;color:#333;margin:5px 0;">{value}</h2>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== 首页概览 ====================
    if page == "🏠 首页概览":
        st.markdown('<h1 class="main-title">🎓 学情与教学评价智能分析系统</h1>', unsafe_allow_html=True)
        st.markdown(f"""
        <p style="font-size:1.1rem;color:#666;line-height:1.8;">
        欢迎，<strong>{st.session_state.username}</strong>！
        本系统基于国产大模型技术，实现<strong>"课后评价→课前学情→连续追踪→阶段总评"</strong>的完整闭环。
        </p>
        """, unsafe_allow_html=True)
        
        # 数据统计
        class_data = get_class_evaluations(subject=subject)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_students = class_data['student_id'].nunique() if not class_data.empty else 0
            render_metric_card("班级学生数", f"{total_students} 人", None, "👥")
        with col2:
            total_lessons = class_data['lesson_id'].nunique() if not class_data.empty else 0
            render_metric_card("教学课时数", f"{total_lessons} 节", None, "📚")
        with col3:
            total_evals = len(class_data) if not class_data.empty else 0
            render_metric_card("评价记录数", f"{total_evals} 条", None, "📝")
        with col4:
            if not class_data.empty:
                dims = get_dimension_cols(class_data)
                avg_score = class_data[dims].mean(axis=1).mean() if dims else 0
                render_metric_card("班级平均分", f"{avg_score:.1f}", None, "📊")
            else:
                render_metric_card("班级平均分", "--", None, "📊")

    elif page == "📐 评价模板":
        st.title("📐 评价维度模板配置")
        st.markdown(f"当前科目：**{subject}**")
        
        tab1, tab2 = st.tabs(["创建新模板", "已有模板管理"])
        
        with tab1:
            st.subheader("创建评价维度模板")
            template_name = st.text_input("模板名称", "例如：语文课-阅读理解评价")
            description = st.text_area("模板说明", "用于评价学生阅读理解能力的维度...")
            
            st.markdown("### 设置评价维度（至少1个）")
            
            if 'dims' not in st.session_state:
                st.session_state.dims = ["知识掌握度", "思维能力", "课堂参与度"]
            
            for i, dim in enumerate(st.session_state.dims):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.session_state.dims[i] = st.text_input(f"维度{i+1}", dim, key=f"dim_{i}")
                with cols[1]:
                    if st.button("删除", key=f"del_{i}"):
                        st.session_state.dims.pop(i)
                        st.rerun()
            
            if st.button("➕ 添加维度"):
                st.session_state.dims.append(f"新维度{len(st.session_state.dims)+1}")
                st.rerun()
            
            st.markdown("### 模板预览")
            preview_df = pd.DataFrame(columns=st.session_state.dims)
            st.dataframe(preview_df)
            
            if st.button("💾 保存模板"):
                if len(set(st.session_state.dims)) != len(st.session_state.dims):
                    st.error("维度名称不能重复！")
                else:
                    template_id = save_template(
                        template_name, subject, st.session_state.dims, 
                        description, "当前教师"
                    )
                    st.success(f"✅ 模板保存成功！ID: {template_id}")
                    st.info("现在可以在'课后评价'中使用此模板")
        
        with tab2:
            st.subheader("已有模板")
            templates = get_templates(subject)
            
            if templates.empty:
                st.info("暂无模板，请先创建")
            else:
                for _, row in templates.iterrows():
                    with st.expander(f"{row['template_name']} (ID:{row['template_id']})"):
                        st.write(f"说明：{row['description']}")
                        st.write("评价维度：")
                        for dim in row['dimensions']:
                            st.markdown(f"- {dim}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("使用此模板", key=f"use_{row['template_id']}"):
                                st.session_state['current_template_id'] = row['template_id']
                                st.success(f"已选择模板：{row['template_name']}")
                                st.info("请切换到'课后评价'页面使用")
                        with col2:
                            if st.button("🗑️ 删除模板", key=f"delete_{row['template_id']}"):
                                success, message = delete_template(row['template_id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.warning(message)

    elif page == "👥 学生管理":
        st.title("👥 学生名单管理")
        st.markdown(f"当前科目：**{subject}**")
        
        # 显示当前选中的班级
        current_class_name = st.session_state.get('current_class_name', None)
        if current_class_name:
            st.markdown(f"当前班级：**{current_class_name}**")
        else:
            st.warning("⚠️ 请先在侧边栏选择或创建班级")
        
        template_df = pd.DataFrame({
            "学号": ["2024001", "2024002"],
            "姓名": ["张三", "李四"],
            "班级": ["高一(1)班", "高一(1)班"]
        })
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ 下载评价表模板",
                template_df.to_csv(index=False).encode('utf-8-sig'),
                "evaluation_template.csv",
                "text/csv"
            )
        with col2:
            st.download_button(
                "⬇️ 下载学生名单模板",
                template_df.to_csv(index=False).encode('utf-8-sig'),
                "student_template.csv",
                "text/csv"
            )
        
        uploaded_file = st.file_uploader("上传学生名单 (Excel/CSV)", type=['csv', 'xlsx'])
        
        if uploaded_file:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("预览数据：")
            st.dataframe(df)
            
            if st.button("✅ 确认导入"):
                # 传入当前班级ID
                current_class_id = st.session_state.get('current_class_id', None)
                import_students(df, subject, current_class_id)
                if current_class_name:
                    st.success(f"成功导入 {len(df)} 名学生到 {subject} 科目 - {current_class_name}！")
                else:
                    st.success(f"成功导入 {len(df)} 名学生到 {subject} 科目！")

    elif page == "📝 课后评价":
        st.title("📝 课后教学评价录入")
        st.markdown(f"当前科目：**{subject}**")
        
        templates = get_templates(subject)
        if templates.empty:
            st.warning("⚠️ 请先创建评价模板（在'评价模板'页面）")
        else:
            template_options = {f"{row['template_name']} (ID:{row['template_id']})": row['template_id'] 
                            for _, row in templates.iterrows()}
            
            # 获取之前选择的模板ID（如果有）
            current_template_id = st.session_state.get('current_template_id')
            
            # 设置默认选中的模板
            default_index = 0
            if current_template_id:
                for i, (name, tid) in enumerate(template_options.items()):
                    if tid == current_template_id:
                        default_index = i
                        break
            
            selected_template_name = st.selectbox("选择评价模板", list(template_options.keys()), index=default_index)
            selected_template_id = template_options[selected_template_name]
            
            # 保存当前选择到session_state
            st.session_state['current_template_id'] = selected_template_id
            template = get_template(selected_template_id)
            dimensions = template['dimensions']
            
            st.success(f"当前模板：{template['template_name']} | 维度：{', '.join(dimensions)}")
            
            col1, col2 = st.columns(2)
            with col1:
                lesson_id = st.text_input("课程编号", value=f"L{datetime.now().strftime('%Y%m%d%H%M')}")
                lesson_name = st.text_input("课程名称")
            with col2:
                eval_date = st.date_input("评价日期", datetime.now())
                evaluator = st.text_input("评价人")
            
            st.markdown(f"### 批量上传评价表（需包含：学号、姓名、{', '.join(dimensions)}）")
            
            template_cols = ["学号", "姓名"] + dimensions + ["评语"]
            template_df = pd.DataFrame(columns=template_cols)
            
            st.download_button(
                "⬇️ 下载当前模板评价表",
                template_df.to_csv(index=False).encode('utf-8-sig'),
                f"评价表_{template['template_name']}.csv",
                "text/csv"
            )
            
            eval_file = st.file_uploader("上传评价表 (CSV/Excel)", type=['csv', 'xlsx'])
            
            if eval_file:
                if eval_file.name.endswith('.csv'):
                    eval_df = pd.read_csv(eval_file)
                else:
                    eval_df = pd.read_excel(eval_file)
                
                st.write("数据预览：")
                st.dataframe(eval_df.head())
                
                st.markdown("### 列名映射确认")
                col_mapping = {}
                col_mapping['学号'] = st.selectbox("学号列", eval_df.columns, index=0)
                col_mapping['姓名'] = st.selectbox("姓名列", eval_df.columns, index=1)
                
                for dim in dimensions:
                    default_idx = 0
                    for i, col in enumerate(eval_df.columns):
                        if dim in col or col in dim:
                            default_idx = i
                            break
                    col_mapping[dim] = st.selectbox(f"【{dim}】列", eval_df.columns, index=default_idx)
                
                col_mapping['评语'] = st.selectbox("评语列（可选）", ['无'] + list(eval_df.columns))
                
                if st.button("🚀 批量保存评价"):
                    success_count = 0
                    for _, row in eval_df.iterrows():
                        scores = {}
                        total = 0
                        count = 0
                        
                        for dim in dimensions:
                            col = col_mapping[dim]
                            if col in row and pd.notna(row[col]):
                                score = float(row[col])
                                scores[dim] = score
                                total += score
                                count += 1
                            else:
                                scores[dim] = 0
                        
                        eval_data = {
                            'student_id': str(row[col_mapping['学号']]),
                            'lesson_id': lesson_id,
                            'lesson_name': lesson_name,
                            'subject': subject,
                            'template_id': selected_template_id,
                            'eval_date': eval_date.strftime('%Y-%m-%d'),
                            'evaluator': evaluator,
                            'scores': scores,
                            'total_score': total / max(count, 1),
                            'comments': row.get(col_mapping['评语'], '') if col_mapping['评语'] != '无' else ''
                        }
                        
                        save_evaluation(eval_data)
                        success_count += 1
                    
                    st.success(f"✅ 成功保存 {success_count} 条评价记录！")
                    st.info(f"💡 使用模板：{template['template_name']}，维度：{', '.join(dimensions)}")

    elif page == "📈 学情追踪":
        st.title("📈 学情实时追踪")
        st.markdown(f"当前科目：**{subject}** | 核心：课后评价→课前学情，连为一体")
        
        class_data = get_class_evaluations(subject=subject)
        
        if class_data.empty:
            st.warning("暂无数据，请先录入评价")
        else:
            students = class_data[['student_id', 'name']].drop_duplicates()
            selected_student = st.selectbox(
                "选择学生",
                students['name'].tolist(),
                format_func=lambda x: f"{x} ({students[students['name']==x]['student_id'].values[0]})"
            )
            
            student_id = students[students['name']==selected_student]['student_id'].values[0]
            student_data = get_student_evaluations(student_id, subject)
            
            if not student_data.empty:
                exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                            'subject', 'template_id', 'eval_date', 'evaluator', 
                            'total_score', 'comments', 'created_at', 'name', 'class_id']
                dimension_cols = [c for c in student_data.columns if c not in exclude_cols]
                
                # 确保只对数值类型的列进行计算
                numeric_cols = student_data[dimension_cols].select_dtypes(include=['number']).columns.tolist()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("评价次数", len(student_data))
                with col2:
                    if numeric_cols:
                        current_avg = student_data[numeric_cols].mean(axis=1).mean()
                    else:
                        current_avg = 0
                    st.metric("当前综合均分", f"{current_avg:.1f}")
                with col3:
                    if len(student_data) >= 2 and numeric_cols:
                        first_avg = student_data.iloc[0][numeric_cols].mean()
                        last_avg = student_data.iloc[-1][numeric_cols].mean()
                        growth = (last_avg - first_avg) / len(student_data)
                    else:
                        growth = 0
                    st.metric("进步率", f"{growth:+.2f}/课时", "📈" if growth > 0 else "📉")
                with col4:
                    if len(student_data) >= 2 and numeric_cols:
                        total_scores = student_data[numeric_cols].mean(axis=1)
                        stability = max(0, 100 - total_scores.std() * 10)
                    else:
                        stability = 100
                    st.metric("稳定性", f"{stability:.1f}%")
                
                tab1, tab2, tab3, tab4 = st.tabs(["能力雷达", "趋势追踪", "热力图", "增值评价"])
                
                with tab1:
                    if dimension_cols:
                        fig = viz.create_radar_chart(student_data, selected_student, dimension_cols)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    if dimension_cols:
                        fig = viz.create_trend_chart(student_data, selected_student, dimension_cols)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    if dimension_cols:
                        fig = viz.create_heatmap(student_data, dimension_cols)
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab4:
                    if numeric_cols and len(student_data) >= 2:
                        # 为单个学生创建增值评价图（显示每次评价的进步情况）
                        student_data_sorted = student_data.sort_values('eval_date')
                        student_data_sorted['total_score'] = student_data_sorted[numeric_cols].mean(axis=1)
                        
                        # 计算增值（与前一次评价相比）
                        student_data_sorted['value_added'] = student_data_sorted['total_score'].diff().fillna(0)
                        
                        fig = px.bar(
                            student_data_sorted,
                            x='eval_date',
                            y='value_added',
                            title=f"{selected_student} - 增值评价（每次评价进步分数）",
                            color='value_added',
                            color_continuous_scale='RdBu',
                            labels={'value_added': '进步分数', 'eval_date': '评价日期'}
                        )
                        fig.add_hline(
                            y=0,
                            line_dash="dash",
                            line_color="gray",
                            annotation_text="基准线",
                            annotation_position="top"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif len(student_data) < 2:
                        st.warning("需要至少两次评价数据才能生成增值评价图")
                    else:
                        st.warning("暂无维度数据")
                
                st.markdown("---")
                st.subheader("🎯 课前学情生成（用于下一次课）")
                
                next_lesson = st.text_input("输入下一次课程名称", "下一课时")
                if st.button("🤖 AI生成课前学情报告"):
                    with st.spinner("AI分析中..."):
                        recent_template_id = student_data.iloc[-1].get('template_id') if not student_data.empty else None
                        report = reporter.generate_pre_lesson_report(
                            student_id, selected_student, subject, next_lesson, 
                            dimension_cols, recent_template_id
                        )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**学情状态：** {report['ai_analysis'].get('status', '分析完成')}")
                        st.warning(f"**风险等级：** {report['ai_analysis'].get('risk_level', '正常')}")
                    with col2:
                        st.success(f"**关注重点：** {report['ai_analysis'].get('focus', '综合发展')}")
                        st.write(f"**AI建议：** {report['ai_analysis'].get('suggestions', '持续观察')}")
                    
                    st.markdown("### 各维度当前水平")
                    dim_scores = report.get('dimension_scores', {})
                    if dim_scores:
                        dim_df = pd.DataFrame([dim_scores]).T
                        dim_df.columns = ['得分']
                        st.bar_chart(dim_df)

    elif page == "📊 数据分析":
        st.title("📊 班级数据分析")
        st.markdown(f"当前科目：**{subject}**")
        
        class_data = get_class_evaluations(subject=subject)
        
        if class_data.empty:
            st.warning("暂无数据")
        else:
            exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                        'subject', 'template_id', 'eval_date', 'evaluator', 
                        'total_score', 'comments', 'created_at', 'name', 'class_id']
            dimensions = [c for c in class_data.columns if c not in exclude_cols]
            # 确保只使用数值类型的列进行计算
            numeric_dims = class_data[dimensions].select_dtypes(include=['number']).columns.tolist()
            
            profile = analytics.generate_class_profile(class_data, numeric_dims)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("班级人数", profile['total_students'])
            with col2:
                st.metric("教学课时", profile['total_lessons'])
            with col3:
                st.metric("班级均分", f"{profile['avg_total_score']:.1f}")
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["学生对比", "维度分布", "维度饼图", "增值评价", "成绩分布"])
            
            with tab1:
                fig = viz.create_class_comparison(class_data, numeric_dims)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                fig = viz.create_dimension_distribution(class_data, numeric_dims)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                if numeric_dims:
                    selected_dim = st.selectbox("选择评价维度", numeric_dims)
                    fig = viz.create_dimension_pie_chart(class_data, selected_dim)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("暂无维度数据")
            
            with tab4:
                if numeric_dims:
                    # 检查是否有学生有多次评价
                    student_eval_counts = class_data.groupby('name').size()
                    students_with_multiple_evals = student_eval_counts[student_eval_counts >= 2]
                    if len(students_with_multiple_evals) >= 1:
                        fig = viz.create_value_added_chart(class_data, numeric_dims)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("需要至少有一个学生有两次以上评价才能生成增值评价图")
                else:
                    st.warning("暂无维度数据")
            
            with tab5:
                dist_df = pd.DataFrame(list(profile['score_distribution'].items()), 
                                    columns=['等级', '人数'])
                fig = px.pie(dist_df, values='人数', names='等级', title="成绩等级分布")
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.subheader("⚠️ 学习预警")
            
            if numeric_dims:
                low_score_students = class_data.groupby('name')[numeric_dims].mean().mean(axis=1)
                risk_students = low_score_students[low_score_students < 70].sort_values()
                
                if not risk_students.empty:
                    risk_df = pd.DataFrame({
                        '学生': risk_students.index,
                        '综合均分': risk_students.values.round(1)
                    })
                    st.dataframe(risk_df, use_container_width=True)
                else:
                    st.success("✅ 班级整体表现良好，暂无预警学生")

    elif page == "📋 阶段总评":
        st.title("📋 阶段总体评价生成")
        st.markdown(f"当前科目：**{subject}** | 经过连续教学过程后的总体评价")
        
        class_data = get_class_evaluations(subject=subject)
        
        if class_data.empty:
            st.warning("暂无数据")
        else:
            students = class_data[['student_id', 'name']].drop_duplicates()
            
            col1, col2 = st.columns(2)
            with col1:
                selected_student = st.selectbox("选择学生", students['name'].tolist())
                student_id = students[students['name']==selected_student]['student_id'].values[0]
            with col2:
                phase_name = st.text_input("阶段名称", "第一学期期中")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("开始日期", datetime.now() - timedelta(days=90))
            with col2:
                end_date = st.date_input("结束日期", datetime.now())
            
            if st.button("📄 生成阶段总评报告"):
                with st.spinner("AI生成详细评价报告..."):
                    phase_eval = reporter.generate_phase_evaluation(
                        student_id, selected_student, subject, 
                        phase_name, start_date.strftime('%Y-%m-%d'), 
                        end_date.strftime('%Y-%m-%d')
                    )
                
                if phase_eval:
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("阶段均分", f"{phase_eval['overall_score']}")
                    with col2:
                        st.metric("综合等级", phase_eval['overall_level'])
                    with col3:
                        student_data = get_student_evaluations(student_id, subject)
                        if not student_data.empty:
                            exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                                        'subject', 'template_id', 'eval_date', 'evaluator', 
                                        'total_score', 'comments', 'created_at', 'name']
                            dimension_cols = [c for c in student_data.columns if c not in exclude_cols]
                            numeric_cols = student_data[dimension_cols].select_dtypes(include=['number']).columns.tolist()
                            growth = analytics.calculate_growth_rate(student_data, numeric_cols)
                        else:
                            growth = 0
                        st.metric("阶段进步率", f"{growth:+.2f}/课时")
                    
                    st.markdown("### 🤖 AI智能评价报告")
                    st.markdown(phase_eval['ai_report'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"**优势领域：** {phase_eval['strength_areas'] or '综合发展均衡'}")
                    with col2:
                        st.error(f"**薄弱环节：** {phase_eval['weakness_areas'] or '暂无显著薄弱项'}")
                    
                    report_text = f"""
                    学情与教学评价智能分析系统 - 阶段总评报告
                    学生：{selected_student}
                    科目：{subject}
                    阶段：{phase_name}
                    时间：{start_date} 至 {end_date}
                    综合评分：{phase_eval['overall_score']}
                    综合等级：{phase_eval['overall_level']}
                    {phase_eval['ai_report']}
                    """
                    
                    st.download_button(
                        "⬇️ 下载评价报告",
                        report_text.encode('utf-8'),
                        f"{selected_student}_{subject}_{phase_name}_评价报告.txt",
                        "text/plain"
                    )
                else:
                    st.error("该时间段内无评价数据")

    elif page == "🤖 AI教学策略":
        st.title("🤖 AI智能教学策略")
        st.markdown(f"当前科目：**{subject}**")
        
        class_data = get_class_evaluations(subject=subject)
        
        if class_data.empty:
            st.warning("暂无数据")
        else:
            lessons = class_data[['lesson_id', 'lesson_name']].drop_duplicates()
            selected_lesson = st.selectbox(
                "选择课时",
                lessons['lesson_name'].tolist(),
                format_func=lambda x: f"{x} ({lessons[lessons['lesson_name']==x]['lesson_id'].values[0]})"
            )
            lesson_id = lessons[lessons['lesson_name']==selected_lesson]['lesson_id'].values[0]
            
            if st.button("🎯 生成教学策略"):
                with st.spinner("AI分析班级学情并生成策略..."):
                    strategy = reporter.generate_class_strategy(
                        lesson_id, subject, selected_lesson
                    )
                
                if strategy:
                    st.markdown("---")
                    st.subheader(f"📚 《{selected_lesson}》教学策略建议")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("班级人数", strategy['class_size'])
                    with col2:
                        st.metric("课时", selected_lesson)
                    
                    st.markdown("### 🤖 AI策略分析")
                    st.markdown(strategy['strategy'])
                    
                    with st.expander("查看详细统计数据"):
                        st.json(strategy['statistics'])
                else:
                    st.error("生成失败，请检查数据")

# 主入口逻辑
if __name__ == "__main__":
    if st.session_state.user_id:
        main_app()
    else:
        login_page()