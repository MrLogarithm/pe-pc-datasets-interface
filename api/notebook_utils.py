import flask_app as api
from ipywidgets import interactive_output, HBox
import ipywidgets as widgets
from matplotlib import pyplot as plt
from IPython.display import display, HTML
import pprint
import re

def format_label( sign ):
    # Lowercase the sign variant annotations:
    sign = re.sub( "~[^ |+.&X]*", lambda m:m.group(0).lower(), sign )
    # Lowercase x, only when it joins a compound:
    sign = re.sub( "([^x])X", "\\1x", sign )
    return sign

def show_result( format_, query, order, numeric, graph, plt_size, length, lines ):
    query = query.upper()
    result = api.get_counts( format_, query, order, numeric, lines )
    if length > 0:
        result = { k:v for k,v in result.items() if len(k.split(" ")) == length }
    if graph == 'graph':
        data = sorted([ (count,format_label(sign)) for sign, count in result.items() ], reverse=True)
        
        if plt_size > len(data):
            plt_size = len(data)
        
        x = range(plt_size)
        y =      [ count for count, _ in data[:plt_size] ][::-1]
        labels = [ sign for _, sign in data[:plt_size] ][::-1]
        plt.figure(figsize=(8,max(5,0.35*plt_size)))
        plt.barh( x, y, tick_label=labels )
        for x_,y_,value in zip(x,y,y):
            plt.text( y_ * 1.01, x_-0.15, value )
        plt.margins(0.1, 0.015)
    else:
        pprint.PrettyPrinter(indent=4).pprint(result)

formatWidget = widgets.Dropdown(
    options=[
        ('Normal','normal'),
        ('Merge sign variants','merge'),
        ('Split compound signs','split'),
        ('Merge variants and split compounds','merge_split')
    ],
    value='normal',
    description='Data format:',
    disabled=False,
)
queryWidget = widgets.Text(
    value='',
    placeholder='filter results',
    description='Search term:',
    disabled=False,
)
orderWidget = widgets.Checkbox(
    value=True,
    description='Word order matters?',
    disabled=False,
    indent=False
)
numericWidget = widgets.Checkbox(
    value=True,
    description='Include numeric signs?',
    disabled=False,
    indent=False
)
linesWidget = widgets.Checkbox(
    value=True,
    description='Count lines instead of tokens?',
    disabled=False,
    indent=False
)
graphWidget = widgets.Dropdown(
    options=[
        'graph',
        'text',
    ],
    value='text',
    description='Output:',
    disabled=False,
)
plt_sizeWidget = widgets.IntSlider(
    min=0, 
    max=50, 
    step=1, 
    value=10, 
    description='Graph size',
    continuous_update=False
)
lengthWidget = widgets.IntSlider(
    min=0, 
    max=15, 
    step=1, 
    value=1, 
    description='Length',
    continuous_update=False
)
    
i = interactive_output(
    show_result, {
        'format_': formatWidget,
        'query': queryWidget,
        'order': orderWidget,
        'numeric': numericWidget, 
        'graph': graphWidget, 
        'plt_size': plt_sizeWidget,
        'length': lengthWidget,
        'lines': linesWidget
    })

def run():
    rows = [ [formatWidget,graphWidget], [queryWidget,plt_sizeWidget], [lengthWidget], [linesWidget], [orderWidget], [numericWidget], [], [i] ]
    for row in rows:
        display(HBox(row))
    display(HTML('<style> .widget-checkbox { margin-left: 70px; } </style>'))