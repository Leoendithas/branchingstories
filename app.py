import streamlit as st
import openai
from streamlit_d3graph import d3graph

# Initialize
d3 = d3graph()
# Load example data
adjmat, df = d3.import_example('karate')

label = df['label'].values
d3.graph(adjmat)
d3.set_node_properties(label=label, color=label, cmap='Set1')
d3.show()

