import gradio as gr
import pandas as pd
import asyncio
from datetime import datetime, timedelta, timezone
import plotly.express as px
import plotly.graph_objects as go
from CosmosDBHandlers.cosmosChatHistoryHandler import ChatMemoryHandlerForAnalytics

class ChatAnalyticsDashboard:
    def __init__(self):
        self.handler = ChatMemoryHandlerForAnalytics()
        
    async def get_chat_statistics(self):
        """Get basic chat statistics - Fixed version"""
        try:
            # Get total chats - this works
            total_query = "SELECT VALUE COUNT(1) FROM c"
            total_chats = list(self.handler.chat_container.query_items(
                query=total_query,
                enable_cross_partition_query=True
            ))[0]
            
            # Get unique sessions - fetch all and count in Python
            session_query = "SELECT c.sessionId FROM c"
            session_results = list(self.handler.chat_container.query_items(
                query=session_query,
                enable_cross_partition_query=True
            ))
            unique_sessions = len(set(item['sessionId'] for item in session_results))
            
            # Get function usage - fetch all and group in Python
            function_query = "SELECT c.functionUsed FROM c"
            function_results = list(self.handler.chat_container.query_items(
                query=function_query,
                enable_cross_partition_query=True
            ))
            
            # Count function usage in Python
            from collections import Counter
            function_counts = Counter(item['functionUsed'] for item in function_results)
            function_usage = [
                {'functionUsed': func, 'count': count} 
                for func, count in function_counts.items()
            ]
            
            return {
                'total_chats': total_chats,
                'unique_sessions': unique_sessions,
                'function_usage': function_usage
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'total_chats': 0, 'unique_sessions': 0, 'function_usage': []}
    
    async def get_recent_chats(self, limit=10):
        """Get recent chat interactions"""
        try:
            query = f"""
            SELECT TOP {limit} c.sessionId, c.question, c.functionUsed, c.answer, c.timestamp
            FROM c
            ORDER BY c.timestamp DESC
            """
            
            results = list(self.handler.chat_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return results
        except Exception as e:
            print(f"Error getting recent chats: {e}")
            return []

    async def get_chat_timeline(self, days=7):
        """Enhanced timeline data with minute-level precision"""
        try:
            start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            query = f"""
            SELECT c.timestamp, c.functionUsed 
            FROM c 
            WHERE c.timestamp >= '{start_date}'
            ORDER BY c.timestamp
            """
            
            results = list(self.handler.chat_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Process for timeline with minute precision
            timeline_data = []
            for item in results:
                date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                timeline_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'hour': date.hour,
                    'minute': date.minute,
                    'datetime': date,
                    'function': item['functionUsed']
                })
            
            return timeline_data
        except Exception as e:
            print(f"Error getting timeline: {e}")
            return []
        
# Initialize dashboard
dashboard = ChatAnalyticsDashboard()

def sync_wrapper(async_func):
    """Wrapper to run async functions in Gradio"""
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(async_func(*args, **kwargs))
    return wrapper

@sync_wrapper
async def update_sql_statistics():
    """Update SQL query statistics """
    stats = await dashboard.handler.get_sql_query_statistics()
    
    # Create success rate chart with correct state values
    if stats['total_queries'] > 0:
        state_data = pd.DataFrame([
            {'State': 'Success', 'Count': stats['success_count']},
            {'State': 'Error', 'Count': stats['error_count']},
            {'State': 'Null', 'Count': stats['null_count']}  # Changed from 'Failed'
        ])

        state_chart = px.pie(state_data, values='Count', names='State', 
                           title='SQL Query Success Rate',
                           color_discrete_map={'Success': '#10b981', 'Error': '#ef4444', 'Null': '#6b7280'})
    else:
        state_chart = px.pie(values=[1], names=['No Data'], title='SQL Query Success Rate')
    
    # Create top questions chart
    if stats['top_questions']:
        questions_df = pd.DataFrame(stats['top_questions'])
        questions_chart = px.bar(questions_df.head(5), x='count', y='question', 
                                orientation='h', title='Top 5 Most Generated Queries')
        questions_chart.update_layout(yaxis={'categoryorder': 'total ascending'})
    else:
        questions_chart = px.bar(x=[0], y=['No Data'], title='Top Generated Queries')
    
    return (
        f"**Total SQL Queries:** {stats['total_queries']}",
        f"**Success Rate:** {stats['success_rate']:.1f}%",
        f"**Error/Null Queries:** {stats['error_count'] + stats['null_count']}",  # Updated label
        state_chart,
        questions_chart
    )



@sync_wrapper
async def get_recent_sql_queries():
    """Get recent SQL query generations"""
    recent = await dashboard.handler.get_recent_sql_queries(limit=15)
    
    if recent:
        recent_data = []
        for query in recent:
            recent_data.append({
                'Original Question': query['originalQuestion'][:60] + '...' if len(query['originalQuestion']) > 60 else query['originalQuestion'],
                'Generated SQL': query['generatedSql'][:80] + '...' if len(query['generatedSql']) > 80 else query['generatedSql'],
                'State': query['state'],
                'Timestamp': datetime.fromisoformat(query['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            })
        
        return pd.DataFrame(recent_data)
    else:
        return pd.DataFrame({'Message': ['No recent SQL queries']})

@sync_wrapper
async def get_sql_error_analysis():
    """Get failed SQL query analysis"""
    errors = await dashboard.handler.get_sql_error_analysis()
    
    if errors:
        error_data = []
        for error in errors[:10]:  # Limit to 10 most recent errors
            error_data.append({
                'Original Question': error['originalQuestion'][:50] + '...' if len(error['originalQuestion']) > 50 else error['originalQuestion'],
                'Generated SQL': error['generatedSql'][:60] + '...' if len(error['generatedSql']) > 60 else error['generatedSql'],
                'State': error['state'],
                'Timestamp': datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            })
        
        return pd.DataFrame(error_data)
    else:
        return pd.DataFrame({'Message': ['No failed queries found']})

@sync_wrapper
async def update_statistics():
    """Update dashboard statistics"""
    stats = await dashboard.get_chat_statistics()
    
    # Create function usage chart
    if stats['function_usage']:
        func_df = pd.DataFrame(stats['function_usage'])
        func_chart = px.pie(func_df, values='count', names='functionUsed', 
                           title='Function Usage Distribution')
    else:
        func_chart = px.pie(values=[1], names=['No Data'], title='Function Usage Distribution')
    
    return (
        f"**Total Chats:** {stats['total_chats']}",
        f"**Unique Sessions:** {stats['unique_sessions']}",
        func_chart
    )


@sync_wrapper
async def update_timeline(days):
    """Enhanced timeline function with adaptive granularity"""
    timeline_data = await dashboard.get_chat_timeline(days)
    
    if not timeline_data:
        # Return empty chart if no data
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No data available for selected period",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        empty_fig.update_layout(title="Chat Activity Timeline")
        return empty_fig
    
    df = pd.DataFrame(timeline_data)
    
    if days > 1:
        # Multi-day view: Group by date for daily line plot
        daily_counts = df.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        timeline_chart = px.line(
            daily_counts, 
            x='date', 
            y='count',
            title=f'Daily Chat Activity - Last {days} Days',
            markers=True,
            line_shape='linear'
        )
        
        timeline_chart.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Chats",
            hovermode='x unified'
        )
        
    # In the single day section of update_timeline:
    else:
        # Single day view: Group by 15-minute intervals
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + 
                                    df['hour'].astype(str) + ':' + 
                                    df['minute'].astype(str) + ':00')
        
        # Create 15-minute intervals
        df['interval'] = df['datetime'].dt.floor('15min')
        interval_counts = df.groupby('interval').size().reset_index(name='count')
        
        timeline_chart = px.line(
            interval_counts,
            x='interval',
            y='count',
            title=f'Chat Activity by 15-min Intervals - {interval_counts.iloc[0]["interval"].strftime("%Y-%m-%d")}',
            markers=True,
            line_shape='linear'
        )
        
        timeline_chart.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of Chats",
            xaxis=dict(
                tickformat='%H:%M',
                dtick=900000  # 15-minute intervals
            ),
            hovermode='x unified'
        )

    return timeline_chart


@sync_wrapper
async def get_faqs():
    """Get semantic FAQs"""
    faqs = await dashboard.handler.get_semantic_faqs(limit=10)
    
    if faqs:
        faq_data = []
        for faq in faqs:
            faq_data.append({
                'Question': faq['representative_question'][:100] + '...' if len(faq['representative_question']) > 100 else faq['representative_question'],
                'Similar Questions Count': len(faq['similar_questions']),
                'Total Occurrences': faq['total_occurrences']
            })
        
        return pd.DataFrame(faq_data)
    else:
        return pd.DataFrame({'Message': ['No FAQ data available']})

@sync_wrapper
async def get_recent_interactions():
    """Get recent chat interactions"""
    recent = await dashboard.get_recent_chats(limit=20)
    
    if recent:
        recent_data = []
        for chat in recent:
            recent_data.append({
                'Session ID': chat['sessionId'][:8] + '...',
                'Question': chat['question'][:50] + '...' if len(chat['question']) > 50 else chat['question'],
                'Function': chat['functionUsed'],
                'Timestamp': datetime.fromisoformat(chat['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            })
        
        return pd.DataFrame(recent_data)
    else:
        return pd.DataFrame({'Message': ['No recent interactions']})

theme = gr.themes.Citrus(
    secondary_hue="amber",
    font=[gr.themes.GoogleFont('Inter'), 'ui-sans-serif', 'system-ui', 'sans-serif'],
    font_mono=[gr.themes.GoogleFont('Roboto Mono'), 'ui-monospace', 'Consolas', 'monospace'],
)

with gr.Blocks(theme=theme, 
                title="TAL Chat Analytics Dashboard") as demo:

    gr.Markdown("# Chat Analytics Dashboard")
    gr.Markdown("### Real-time analytics for TAL Chatbot")
    
    with gr.Row():
        total_chats = gr.Markdown("**Total Chats:** Loading...")
        unique_sessions = gr.Markdown("**Unique Sessions:** Loading...")

    with gr.Tabs():
        with gr.TabItem("Function Usage Distribution"):
            function_chart = gr.Plot(label="Function Usage Distribution")

        with gr.TabItem("📈 Timeline Analysis"):
            days_slider = gr.Slider(minimum=1, maximum=30, value=7, step=1, 
                                  label="Days to analyze")
            with gr.Row():
                timeline_plot = gr.Plot(label="Daily Chat Activity")
        
        with gr.TabItem("❓ Frequently Asked Questions"):
            faq_table = gr.DataFrame(label="Semantic FAQs", interactive=False)
        
        with gr.TabItem("💬 Recent Interactions"):
            recent_table = gr.DataFrame(label="Recent Chat Interactions", interactive=False)

        with gr.TabItem("🔍 SQL Query Analytics", elem_id="sql-tab"):
            # SQL Statistics Section
            gr.Markdown("### 📊 SQL Generation Statistics")
            with gr.Row():
                with gr.Column(elem_classes="stats-card"):
                    total_sql_queries = gr.Markdown("**Total SQL Queries:** Loading...")
                with gr.Column(elem_classes="stats-card"):
                    sql_success_rate = gr.Markdown("**Success Rate:** Loading...")
                with gr.Column(elem_classes="stats-card"):
                    failed_sql_queries = gr.Markdown("**Failed Queries:** Loading...")
            
            # SQL Charts Section
            with gr.Row():
                with gr.Column(elem_classes="plot-container"):
                    sql_state_chart = gr.Plot(label="SQL Query Success Distribution")
                with gr.Column(elem_classes="plot-container"):
                    top_questions_chart = gr.Plot(label="Most Generated Queries")
            
            # Recent SQL Queries Section
            gr.Markdown("### 📝 Recent SQL Generations")
            with gr.Column(elem_classes="plot-container"):
                recent_sql_table = gr.DataFrame(
                    label="Latest SQL Query Generations", 
                    interactive=False,
                    elem_classes="dataframe"
                )
            
            # Error Analysis Section
            gr.Markdown("### ⚠️ Failed Query Analysis")
            with gr.Column(elem_classes="plot-container"):
                sql_errors_table = gr.DataFrame(
                    label="Recent Failed SQL Queries", 
                    interactive=False,
                    elem_classes="dataframe"
                )
    refresh_btn = gr.Button("🔄 Refresh Dashboard", variant="primary")
    
    
# Update event handlers
    demo.load(update_sql_statistics, outputs=[total_sql_queries, sql_success_rate, failed_sql_queries, sql_state_chart, top_questions_chart])
    demo.load(get_recent_sql_queries, outputs=[recent_sql_table])
    demo.load(get_sql_error_analysis, outputs=[sql_errors_table])

    refresh_btn.click(update_sql_statistics, outputs=[total_sql_queries, sql_success_rate, failed_sql_queries, sql_state_chart, top_questions_chart])
    refresh_btn.click(get_recent_sql_queries, outputs=[recent_sql_table])
    refresh_btn.click(get_sql_error_analysis, outputs=[sql_errors_table])

    days_slider.change(update_timeline, inputs=[days_slider], 
                        outputs=[timeline_plot])

    # Auto-refresh components
   
    # # Event handlers
    demo.load(update_statistics, outputs=[total_chats, unique_sessions, function_chart])
    demo.load(lambda: update_timeline(7), outputs=[timeline_plot])
    demo.load(get_faqs, outputs=[faq_table])
    demo.load(get_recent_interactions, outputs=[recent_table])
    
    refresh_btn.click(update_statistics, outputs=[total_chats, unique_sessions, function_chart])
    refresh_btn.click(lambda: update_timeline(7), outputs=[timeline_plot])
    refresh_btn.click(get_faqs, outputs=[faq_table])
    refresh_btn.click(get_recent_interactions, outputs=[recent_table])
    
    

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
