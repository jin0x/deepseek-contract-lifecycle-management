import plotly.graph_objects as go

def create_timeline_chart(result):
    """Create an enhanced timeline visualization"""
    all_dates = []
    date_labels = []
    for clause in result.document.clauses:
        if clause.related_dates:
            for date in clause.related_dates:
                all_dates.append(date)
                date_labels.append(clause.clause_name)

    if not all_dates:
        return None

    fig = go.Figure(data=[go.Scatter(
        x=all_dates,
        y=date_labels,
        mode='markers+text',
        marker=dict(
            size=15,
            color='#66B2FF',
            symbol='diamond',
            line=dict(color='#3399FF', width=2)
        ),
        text=all_dates,
        textposition="top center",
        textfont=dict(size=12)
    )])

    fig.update_layout(
        title={
            'text': "Contract Timeline",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Date",
        yaxis_title="Clause",
        height=max(300, len(all_dates) * 50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    return fig
