import plotly.express as px
import plotly.graph_objects as go

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
        fig = px.line(
            student_df,
            x='eval_date',
            y='total_score',
            title=f"{student_name} - 学习趋势追踪",
            labels={'total_score': '综合评分', 'eval_date': '日期'},
            markers=True
        )
        fig.add_traces(go.Scatter(
            x=student_df['eval_date'],
            y=student_df['total_score'].rolling(window=3, min_periods=1).mean(),
            mode='lines',
            name='3次移动平均',
            line=dict(dash='dash', color='red')
        ))
        fig.update_layout(yaxis_range=[0, 100])
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