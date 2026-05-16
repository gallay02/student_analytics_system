import streamlit as st
import pandas as pd
import plotly.express as px  # 添加这行
from datetime import datetime, timedelta
from database import (
    init_database, import_students, save_evaluation, 
    get_student_evaluations, get_class_evaluations,
    save_template, get_templates, get_template,
    save_learning_status, save_phase_evaluation
)
from analytics import LearningAnalytics
from visualizations import LearningVisualizer
from reports import ReportGenerator
from config import SCORE_LEVELS

st.set_page_config(
    page_title="学情与教学评价智能分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_database()
analytics = LearningAnalytics()
viz = LearningVisualizer()
reporter = ReportGenerator()

st.sidebar.title("📚 智能学情分析系统")
st.sidebar.markdown("---")

subject = st.sidebar.selectbox(
    "选择科目",
    ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "其他"]
)

page = st.sidebar.radio(
    "功能导航",
    ["🏠 首页", "📐 评价模板", "👥 学生管理", "📝 课后评价", "📈 学情追踪", 
     "📊 数据分析", "📋 阶段总评", "🤖 AI教学策略"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**系统特点：**
- 课后评价→课前学情，连续追踪
- 适用于任何科目
- 接入国产大模型AI分析
- 数据可视化呈现
""")

if page == "🏠 首页":
    st.title("🎓 学情与教学评价智能分析系统")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("系统状态", "运行中", "✅")
    with col2:
        st.metric("支持科目", "全科目通用", "📚")
    with col3:
        st.metric("AI模型", "国产大模型", "🤖")
    
    st.markdown("""
    ### 系统核心功能
    本系统实现了**"课后评价→课前学情→连续追踪→阶段总评"**的闭环：
    1. **📝 课后评价录入** - 教师上传评价表，系统自动计算总分
    2. **📈 学情实时追踪** - 上一次课后评价自动成为下一次课前学情
    3. **📊 数据可视化** - 雷达图、趋势图、热力图等多维呈现
    4. **🤖 AI智能诊断** - 接入国产大模型，生成学情报告和教学策略
    5. **📋 阶段总评生成** - 连续教学过程后自动生成总体评价
    """)

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
                    
                    if st.button("使用此模板", key=f"use_{row['template_id']}"):
                        st.session_state['current_template_id'] = row['template_id']
                        st.success(f"已选择模板：{row['template_name']}")
                        st.info("请切换到'课后评价'页面使用")

elif page == "👥 学生管理":
    st.title("👥 学生名单管理")
    st.markdown(f"当前科目：**{subject}**")
    
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
            import_students(df, subject)
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
        
        selected_template_name = st.selectbox("选择评价模板", list(template_options.keys()))
        selected_template_id = template_options[selected_template_name]
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
                          'total_score', 'comments', 'created_at', 'name']
            dimension_cols = [c for c in student_data.columns if c not in exclude_cols]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("评价次数", len(student_data))
            with col2:
                current_avg = student_data[dimension_cols].mean(axis=1).mean()
                st.metric("当前综合均分", f"{current_avg:.1f}")
            with col3:
                if len(student_data) >= 2:
                    first_avg = student_data.iloc[0][dimension_cols].mean()
                    last_avg = student_data.iloc[-1][dimension_cols].mean()
                    growth = (last_avg - first_avg) / len(student_data)
                else:
                    growth = 0
                st.metric("进步率", f"{growth:+.2f}/课时", "📈" if growth > 0 else "📉")
            with col4:
                if len(student_data) >= 2:
                    total_scores = student_data[dimension_cols].mean(axis=1)
                    stability = max(0, 100 - total_scores.std() * 10)
                else:
                    stability = 100
                st.metric("稳定性", f"{stability:.1f}%")
            
            tab1, tab2, tab3 = st.tabs(["能力雷达", "趋势追踪", "热力图"])
            
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
                      'total_score', 'comments', 'created_at', 'name']
        dimensions = [c for c in class_data.columns if c not in exclude_cols]
        
        profile = analytics.generate_class_profile(class_data, dimensions)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("班级人数", profile['total_students'])
        with col2:
            st.metric("教学课时", profile['total_lessons'])
        with col3:
            st.metric("班级均分", f"{profile['avg_total_score']:.1f}")
        
        tab1, tab2, tab3 = st.tabs(["学生对比", "维度分布", "成绩分布"])
        
        with tab1:
            fig = viz.create_class_comparison(class_data, dimensions)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = viz.create_dimension_distribution(class_data, dimensions)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            dist_df = pd.DataFrame(list(profile['score_distribution'].items()), 
                                  columns=['等级', '人数'])
            fig = px.pie(dist_df, values='人数', names='等级', title="成绩等级分布")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⚠️ 学习预警")
        
        if dimensions:
            low_score_students = class_data.groupby('name')[dimensions].mean().mean(axis=1)
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
                    exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                                  'subject', 'template_id', 'eval_date', 'evaluator', 
                                  'total_score', 'comments', 'created_at', 'name']
                    dimension_cols = [c for c in student_data.columns if c not in exclude_cols]
                    growth = analytics.calculate_growth_rate(student_data, dimension_cols)
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

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 学情与教学评价智能分析系统 | 基于国产大模型")