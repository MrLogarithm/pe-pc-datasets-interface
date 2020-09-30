import count as api
from ipywidgets import interactive_output, HBox
import ipywidgets as widgets
from matplotlib import pyplot as plt
from IPython.display import display, HTML
import re

formatWidget = widgets.RadioButtons( 
    options=[('none','normal'), ('merge sign variants','merge'), ('split compound signs','split'),('merge variants and split compounds','merge_split')], 
    value='merge_split',
#     value='merge variants and split compounds',
    description ='',
    disabled=False
)
# widgets.Dropdown(
#     options=[
#         ('Normal','normal'),
#         ('Merge sign variants','merge'),
#         ('Split compound signs','split'),
#         ('Merge variants and split compounds','merge_split')
#     ],
#     value='merge_split',
#     description='Variants and compounds:',
#     disabled=False,
# )
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
    value=False,
    description='Count lines instead of tokens?',
    disabled=False,
    indent=False
)
graphWidget = widgets.Dropdown(
    options=[
        'graph',
        'text',
    ],
    value='graph',
    description='',
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
adminWidget = widgets.Checkbox(
    value=True,
    description='administrative',
    disabled=False,
    indent=False
)
lexWidget = widgets.Checkbox(
    value=True,
    description='lexical',
    disabled=False,
    indent=False
)
miscWidget = widgets.Checkbox(
    value=True,
    description='other (school, legal, uncertain)',
    disabled=False,
    indent=False
)
urukiiiWidget = widgets.Checkbox(
    value=True,
    description='Uruk III',
    disabled=False,
    indent=False
)
urukivWidget = widgets.Checkbox(
    value=True,
    description='Uruk IV',
    disabled=False,
    indent=False
)
urukvWidget = widgets.Checkbox(
    value=False,
    description='Uruk V',
    disabled=False,
    indent=False
)
textOrderWidget = widgets.Dropdown(
    options=[
        ('frequency','freq'),
        ('alphanumeric','alpha'),
    ],
    value='freq',
    description='Order by...',
    disabled=False,
)
locations = sorted(list(set([text['provenience'] for text in api.corpus])))
locationWidgets = [widgets.Checkbox(
    value=True,
    description=loc if loc != '' else '[no provenience recorded]',
    disabled=False,
    indent=False
) for loc in locations]
# provWidget = widgets.Dropdown(
#     options=locations,
# #     value='freq',
#     description='Order by...',
#     disabled=False,
# )





def format_label( sign ):
    # Lowercase the sign variant annotations:
    sign = re.sub( "~[^ |+.&X]*", lambda m:m.group(0).lower(), sign )
    # Lowercase x, only when it joins a compound:
    sign = re.sub( "([^x|])X", "\\1x", sign )
    return sign

def show_result( format_, query, order, numeric, graph, plt_size, length, lines, urukiii, urukiv, urukv, textOrder, admin, lexical, misc, **locations ):
    query = query.upper()
    periods = []

    if graph != 'graph':
        plt_sizeWidget.disabled = True
        plt_sizeWidget.layout.visibility = 'hidden'
    else:
        plt_sizeWidget.disabled = False
        plt_sizeWidget.layout.visibility = 'visible'
    
    if urukiii:
        periods += ['uruk iii']
    if urukiv:
        periods += ['uruk iv']
    if urukv:
        periods += ['uruk v']

    genre = []
    if admin:
        genre += ['administrative']
    if lexical:
        genre += ['lexical']
    if misc:
        genre += ['school', 'uncertain', 'legal', 'literary', 'votive']
    
        
    provenience = []
    for location, include in locations.items():
        if include:
            provenience.append(location)

    result = api.get_counts( format_, query, order, numeric, lines, periods, genre, provenience )
    if length > 0:
        result = { k:v for k,v in result.items() if len(k.split(" ")) == length }
    if graph == 'graph':
        data = sorted([ (count,format_label(sign)) for sign, count in result.items() ], reverse=True)
        if textOrder == 'alpha':
            data = sorted(data, key=lambda x: x[1])
        
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
        print("{")
        if textOrder == 'alpha':
            data = sorted([ (sign, count) for sign,count in result.items() ])
            for sign, count in data:
                print("\t\"%s\": %d,"%(sign,count))
        else:
            data = sorted([ (count, sign) for sign,count in result.items() ],reverse=True)
            for count, sign in data:
                print("\t\"%s\": %d,"%(sign,count))
        print("}")






i = interactive_output(
    show_result, dict({
        'format_': formatWidget,
        'query': queryWidget,
        'order': orderWidget,
        'numeric': numericWidget, 
        'graph': graphWidget, 
        'admin': adminWidget,
        'lexical': lexWidget,
        'misc': miscWidget,
        'plt_size': plt_sizeWidget,
        'length': lengthWidget,
        'lines': linesWidget,
        'urukiii': urukiiiWidget,
        'urukiv': urukivWidget,
        'urukv': urukvWidget,
        'textOrder': textOrderWidget,
    }, **{locations[i]:locationWidgets[i] for i in range(len(locations))}))

def run():
    rows = [ 
        [queryWidget],
        [widgets.Label(value="Preprocessing:"),formatWidget],
        [],
        [lengthWidget],
        [linesWidget], 
        [orderWidget], 
        [numericWidget],
        [],
        [widgets.Label(value="Included genres:")],
        [adminWidget, lexWidget, miscWidget],
        [],
        [widgets.Label(value="Included periods:")],
        [urukiiiWidget,urukivWidget,urukvWidget], 
        [],
        [widgets.Label(value="Included locations:")],
    ] + [
        locationWidgets[i:i+2] for i in range(0,len(locationWidgets),2)
    ] + [
        [],
        [widgets.Label(value="Output format:"),graphWidget], 
        [],
        [textOrderWidget],
        [],
        [plt_sizeWidget], 
        [], 
        [i] 
    ]
    for row in rows:
        display(HBox(row))
    display(HTML('<style> .widget-checkbox { margin-left: 70px; } </style>'))
