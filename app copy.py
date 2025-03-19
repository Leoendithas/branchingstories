import streamlit as st
from openai import OpenAI
import json
from streamlit.components.v1 import html

# OpenAI API key (make sure to set this as an environment variable or replace it directly)
OpenAI.api_key = st.secrets['OPENAI_API_KEY']


def get_story_json(prompt):
    response = OpenAI.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a branching story generator."},
            {"role": "user", "content": prompt}
        ]
    )
    story_json = response['choices'][0]['message']['content']
    return json.loads(story_json)


# Streamlit UI
st.title('Branching Story Visualizer')
prompt = st.text_area('Enter your prompt for the branching story:',
                      "Generate a branching story based on a student's decisions.")

if st.button('Generate Story'):
    try:
        story_data = get_story_json(prompt)

        # D3.js HTML rendering
        html_code = f'''
            <div id="d3-container"></div>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <script>
                const data = {json.dumps(story_data)};

                const width = 800, height = 600;
                const svg = d3.select("#d3-container").append("svg")
                    .attr("width", width)
                    .attr("height", height);

                const root = d3.hierarchy(data);
                const treeLayout = d3.tree().size([width - 100, height - 100]);
                treeLayout(root);

                const g = svg.append("g").attr("transform", "translate(50,50)");

                // Links
                g.selectAll(".link")
                    .data(root.links())
                    .enter()
                    .append("line")
                    .attr("class", "link")
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y)
                    .attr("stroke", "#999");

                // Nodes
                const nodes = g.selectAll(".node")
                    .data(root.descendants())
                    .enter()
                    .append("g")
                    .attr("class", "node")
                    .attr("transform", d => `translate(${d.x},${d.y})`);

                nodes.append("circle")
                    .attr("r", 5)
                    .attr("fill", "#69b3a2");

                nodes.append("text")
                    .attr("dy", -10)
                    .attr("x", 6)
                    .text(d => d.data.name);
            </script>
        '''

        # Render HTML with D3.js
        html(html_code, height=700)

    except Exception as e:
        st.error(f"An error occurred: {e}")
