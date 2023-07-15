import re
import plotly.graph_objects as go
import plotly.express as px

def get_sentence(text, index):
    sentence = text[max(0, text.rfind('.', 0, index)) + 1 : text.find('.', index) + 1].strip()
    return sentence

fig = go.Figure()

with open(r"C:\PythonProjects\BibleViz\nt_bible_clean.txt", "r") as file:
    text = file.read()

characters = ["Jesus", "Christ", "Peter", "Paul", "John the Baptist", "John",  "Mary Magdalene", "Mary", "Judas Iscariot", 'Judas', "Pilate", "Matthew", "Mark", "Luke", "James", "Thomas", "Satan"]
colors = px.colors.qualitative.Plotly

chapters = [
    'The Gospel According to Saint Matthew',
    'The Gospel According to Saint Mark',
    'The Gospel According to Saint Luke',
    'The Gospel According to Saint John',
    'The Acts of the Apostles',
    'The Epistle of Paul the Apostle to the Romans',
    'The First Epistle of Paul the Apostle to the Corinthians',
    'The Second Epistle of Paul the Apostle to the Corinthians',
    'The Epistle of Paul the Apostle to the Galatians',
    'The Epistle of Paul the Apostle to the Ephesians',
    'The Epistle of Paul the Apostle to the Philippians',
    'The Epistle of Paul the Apostle to the Colossians',
    'The First Epistle of Paul the Apostle to the Thessalonians',
    'The Second Epistle of Paul the Apostle to the Thessalonians',
    'The First Epistle of Paul the Apostle to Timothy',
    'The Second Epistle of Paul the Apostle to Timothy',
    'The Epistle of Paul the Apostle to Titus',
    'The Epistle of Paul the Apostle to Philemon',
    'The Epistle of Paul the Apostle to the Hebrews',
    'The General Epistle of James',
    'The First Epistle General of Peter',
    'The Second General Epistle of Peter',
    'The First Epistle General of John',
    'The Second Epistle General of John',
    'The Third Epistle General of John',
    'The General Epistle of Jude',
    'The Revelation of Saint John the Divine'
]
# Calculate the new total length of the text
total_length = len(text)

character_positions = {character: [] for character in characters}
for character in characters:
    if character == "Peter":
        # If the character is "Peter", also search for "Simon"
        character_positions[character] = [m.start() for m in re.finditer(rf"\b{'Peter'}\b|\b{'Simon'}\b", text, re.IGNORECASE)]
    elif character == "Mary Magdalene":
        # If the character is "Mary Magdalene", only match "Mary Magdalene", not "Mary"
        character_positions[character] = [m.start() for m in re.finditer(rf"\b{character}\b", text, re.IGNORECASE)]
        # Remove the mentions of "Mary Magdalene" from "Mary"
        character_positions["Mary"] = [pos for pos in character_positions["Mary"] if pos not in character_positions["Mary Magdalene"]]
    elif character == "John the Baptist":
        # If the character is "John the Baptist", only match "John the Baptist", not "John"
        character_positions[character] = [m.start() for m in re.finditer(rf"\b{character}\b", text, re.IGNORECASE)]
        # Remove the mentions of "John the Baptist" from "John"
        character_positions["John"] = [pos for pos in character_positions["John"] if pos not in character_positions["John the Baptist"]]
    elif character == "Judas Iscariot":
        # If the character is "Judas Iscariot", only match "Judas Iscariot", not "Judas"
        character_positions[character] = [m.start() for m in re.finditer(rf"\b{character}\b", text, re.IGNORECASE)]
        # Remove the mentions of "Judas Iscariot" from "Judas"
        character_positions["Judas"] = [pos for pos in character_positions["Judas"] if
                                       pos not in character_positions["Judas Iscariot"]]
    else:
        character_positions[character] = [m.start() for m in re.finditer(rf"\b{character}\b", text, re.IGNORECASE)]

chapter_positions = {chapter: text.find(chapter) / total_length * 100 for chapter in chapters}

chapter_names = ['Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '', '', '', 'The Epistles', '', '', '', '', '', '', '', '', 'Hebrews', '', '', '', '', '', '', '', 'Revelations']

# chapter_xs = tuple(value/100 for value in chapter_positions.values())


chapter_xs = tuple(chapter_positions.values())


# chapter_xs = tuple(range(0,27))

for spot, character in enumerate(characters):
    indices = character_positions[character]
    sentences = []
    for i in indices:
        sentences.append(get_sentence(text, i))
    percentages = [100 * i / len(text) for i in indices]

    fig.add_trace(go.Scatter(x=percentages, y=[character]*len(indices), mode='markers', name=character, text=sentences, hovertemplate="%{text}<extra></extra>", marker=dict(color=colors[spot % len(colors)])))

firstcolor = "mediumseagreen"
secondcolor = "peachpuff"
for i in range(len(chapters) - 1):
    fig.add_shape(type="rect", xref="x", yref="paper", x0=chapter_xs[i], y0=0, x1=chapter_xs[i + 1], y1=1, fillcolor=firstcolor if i % 2 == 0 else secondcolor, opacity=0.25, line_width=0)

# Color in the last book, Revelations, independently:
fig.add_shape(type="rect", xref="x", yref="paper", x0=chapter_xs[26], y0=0, x1=100, y1=1,
              fillcolor=firstcolor, opacity=0.25, line_width=0)
#
# for i in range(len(chapter_names)):
#     fig.add_annotation(x=chapter_xs[i], y=1.05, yref="paper", text=chapter_names[i], showarrow=False)

#Trying to add chapter names and lines at the same time:

for i in range(len(chapter_names)):
    fig.add_shape(
        type="line",
        xref="x",
        yref="paper",
        x0=chapter_xs[i],
        y0=0,
        x1=chapter_xs[i],
        y1=1,
        line=dict(
            color="peru",
            width=1.5,
        ),
    )
    fig.add_annotation(x=chapter_xs[i], y=1.05, yref="paper", text=chapter_names[i], showarrow=False,
                       font=dict(color='peru'))

fig.update_layout(
    title={
        'text': "Mentions of Each Being Throughout the Bible",
        'x': 0.5,
        'xanchor': 'center',
        'font': dict(color='maroon')
    },
    titlefont=dict(color='maroon'),
    showlegend=False,
    xaxis_title="Position in Bible (%)",
    xaxis_color='maroon',
    yaxis_title="Being",
    yaxis_color='maroon',
    hoverlabel=dict(font_size=16),
    hovermode="closest",
    yaxis=dict(
        tickmode='array',
        tickvals=characters,
        ticktext=characters
    ),
    xaxis=dict(
        range=[0, 100],  # set the x-axis range to match your data
    ),
    autosize=True,  # disable autosizing
    margin=dict(
        l=50,  # left margin
        r=50,  # right margin
        b=100,  # bottom margin
        t=100,  # top margin
        pad=0  # padding
    ),
)
fig.update_layout(
    yaxis=dict(
        tickfont=dict(
            color='maroon'
        )
    )
)
fig.show()
