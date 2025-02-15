import plotly.graph_objects as go

def create_confidence_chart(result):
    """Create an enhanced bar chart for confidence scores"""
    confidence_scores = [clause.metadata.confidence_score for clause in result.document.clauses]
    clause_names = [clause.clause_name for clause in result.document.clauses]

    fig = go.Figure(data=[go.Bar(
        x=clause_names,
        y=confidence_scores,
        marker_color='#66B2FF',
        marker_line_color='#3399FF',
        marker_line_width=1.5,
        opacity=0.8
    )])

    fig.update_layout(
        title={
            'text': "Clause Analysis Confidence Scores",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Clause Name",
        yaxis_title="Confidence Score",
        height=400,
        xaxis_tickangle=-45,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
