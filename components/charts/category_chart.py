import plotly.graph_objects as go
import pandas as pd

def create_clause_category_chart(result):
    """Create an enhanced donut chart for clause categories"""
    categories = [clause.clause_category for clause in result.document.clauses]
    category_counts = pd.Series(categories).value_counts()

    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF']
    fig = go.Figure(data=[go.Pie(
        labels=category_counts.index,
        values=category_counts.values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside',
        pull=[0.1] * len(category_counts)
    )])

    fig.update_layout(
        title={
            'text': "Distribution of Clause Categories",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        showlegend=False,
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig