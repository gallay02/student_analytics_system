import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

class LearningVisualizer:
    @staticmethod
    def create_radar_chart(student_df, student_name, dimensions):
        avg_scores = student_df[dimensions].mean()
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(avg_scores.values) + [avg_scores.values[0]],
            theta=list(avg_scores.index) + [avg_scores.index[0]],
            fill='toself',
            name=student_name
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title=f"{student_name} - 能力维度雷达图"
        )
        return fig
    
    @staticmethod
    def create_trend_chart(student_df, student_name, dimensions):
        student_df = student_df.sort_values('eval_date')
        student_df['total_score'] = student_df[dimensions].mean(axis=1)
        
        fig = go.Figure()
        
        # 添加综合评分趋势线
        fig.add_trace(go.Scatter(
            x=student_df['eval_date'],
            y=student_df['total_score'],
            mode='lines+markers',
            name='综合评分',
            line=dict(width=3, color='blue')
        ))
        
        # 添加3次移动平均线
        fig.add_trace(go.Scatter(
            x=student_df['eval_date'],
            y=student_df['total_score'].rolling(window=3, min_periods=1).mean(),
            mode='lines',
            name='3次移动平均',
            line=dict(dash='dash', color='red', width=2)
        ))
        
        # 添加各维度趋势线
        for dim in dimensions[:4]:  # 最多显示4个维度
            fig.add_trace(go.Scatter(
                x=student_df['eval_date'],
                y=student_df[dim],
                mode='lines',
                name=dim,
                line=dict(width=2, dash='dot'),
                opacity=0.6
            ))
        
        fig.update_layout(
            title=f"{student_name} - 学习趋势追踪",
            xaxis_title='日期',
            yaxis_title='得分',
            yaxis_range=[0, 100],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig
    
    @staticmethod
    def create_heatmap(student_df, dimensions):
        pivot_df = student_df.pivot_table(
            values=dimensions,
            index='lesson_name',
            aggfunc='mean'
        )
        fig = px.imshow(
            pivot_df,
            labels=dict(x="评价维度", y="课程", color="得分"),
            title="各课程维度得分热力图",
            color_continuous_scale="RdYlGn",
            range_color=[0, 100]
        )
        return fig
    
    @staticmethod
    def create_class_comparison(class_df, dimensions):
        student_summary = class_df.groupby('name')[dimensions].mean().mean(axis=1).reset_index()
        student_summary.columns = ['姓名', '平均分']
        student_summary = student_summary.sort_values('平均分', ascending=True)
        fig = px.bar(
            student_summary,
            x='平均分',
            y='姓名',
            orientation='h',
            title="班级学生综合评分对比",
            color='平均分',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        return fig
    
    @staticmethod
    def create_dimension_distribution(class_df, dimensions):
        melted_df = class_df.melt(
            id_vars=['name'],
            value_vars=dimensions,
            var_name='维度',
            value_name='得分'
        )
        fig = px.box(
            melted_df,
            x='维度',
            y='得分',
            title="班级各维度得分分布",
            points="all"
        )
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    
    @staticmethod
    def create_dimension_pie_chart(class_df, dimension_name):
        """创建单个维度的班级学生成绩分布饼状图"""
        # 将分数分为5个等级
        bins = [0, 60, 70, 80, 90, 100]
        labels = ['不及格(<60)', '及格(60-70)', '中等(70-80)', '良好(80-90)', '优秀(90-100)']
        
        # 计算每个等级的人数
        scores = class_df[dimension_name].dropna()
        score_counts = pd.cut(scores, bins=bins, labels=labels, include_lowest=True).value_counts()
        
        # 确保所有标签都存在
        for label in labels:
            if label not in score_counts:
                score_counts[label] = 0
        
        score_counts = score_counts.reindex(labels)
        
        fig = px.pie(
            values=score_counts.values,
            names=score_counts.index,
            title=f"{dimension_name} - 成绩等级分布",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    
    @staticmethod
    def create_value_added_chart(class_df, dimensions):
        """创建增值评价图（展示学生进步情况）"""
        # 获取所有学生列表
        all_students = class_df['name'].unique()
        
        # 计算每个学生第一次和最后一次评价的分数
        student_first_last = class_df.groupby('name').agg(
            first_date=('eval_date', 'min'),
            last_date=('eval_date', 'max')
        ).reset_index()
        
        # 获取第一次评价的分数
        first_scores = class_df[class_df['eval_date'].isin(student_first_last['first_date'])].copy()
        first_scores['total_score'] = first_scores[dimensions].mean(axis=1)
        
        # 获取最后一次评价的分数
        last_scores = class_df[class_df['eval_date'].isin(student_first_last['last_date'])].copy()
        last_scores['total_score'] = last_scores[dimensions].mean(axis=1)
        
        # 合并数据
        value_added_df = pd.merge(
            first_scores[['name', 'total_score']],
            last_scores[['name', 'total_score']],
            on='name',
            suffixes=('_first', '_last'),
            how='outer'  # 使用outer join确保所有学生都包含
        )
        
        # 处理只有一次评价的学生（增值为0）
        value_added_df['total_score_first'] = value_added_df['total_score_first'].fillna(value_added_df['total_score_last'])
        value_added_df['total_score_last'] = value_added_df['total_score_last'].fillna(value_added_df['total_score_first'])
        
        # 计算增值分数
        value_added_df['value_added'] = value_added_df['total_score_last'] - value_added_df['total_score_first']
        value_added_df = value_added_df.sort_values('value_added', ascending=True)
        
        fig = px.bar(
            value_added_df,
            x='value_added',
            y='name',
            orientation='h',
            title="学生增值评价（进步分数）",
            color='value_added',
            color_continuous_scale='RdBu',
            labels={'value_added': '进步分数', 'name': '学生姓名'}
        )
        
        # 添加参考线（0分）
        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="gray",
            annotation_text="基准线",
            annotation_position="top"
        )
        
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            coloraxis_colorbar=dict(title='进步分数')
        )
        return fig