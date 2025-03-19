import streamlit as st
from openai import OpenAI
import json
from streamlit.components.v1 import html

# Initialize the OpenAI client correctly
client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

def get_story_json(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a branching story generator. Always respond with valid JSON that represents a tree structure for a branching story. The JSON should have a 'name' field for the story node and a 'children' array for branching options."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.1
    )
    story_content = response.choices[0].message.content
    
    # Debug the response
    st.write("Raw API response:")
    st.write(story_content)
    
    # Try to clean the response if it's not pure JSON
    # Sometimes the API might return markdown-formatted JSON or add explanatory text
    if not story_content.strip().startswith('{'):
        # Try to extract JSON from the response (if wrapped in ```json or similar)
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', story_content)
        if json_match:
            story_content = json_match.group(1)
    
    try:
        return json.loads(story_content)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON: {e}")
        # Provide a fallback simple JSON structure
        return {
            "name": "Story start",
            "children": [
                {"name": "Error: Could not generate valid story JSON. Please try again."}
            ]
        }


# Streamlit UI
st.title('Branching Story Visualizer')
prompt = st.text_area('Enter your prompt for the branching story:',
                      "Generate a branching story based on a student's decisions.")

if st.button('Generate Story'):
    try:
        story_data = get_story_json(prompt)

        # Log the structure before visualization
        st.write("Data structure for visualization:")
        st.write(story_data)
        
        # D3.js HTML rendering
        html_code = f'''
            <div id="d3-container"></div>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <script>
                const data = {json.dumps(story_data)};
                console.log("Data received in D3:", data);

                const width = 800, height = 600;
                const svg = d3.select("#d3-container").append("svg")
                    .attr("width", width)
                    .attr("height", height);

                // Make sure we have valid data structure
                if (!data || typeof data !== 'object') {{
                    svg.append("text")
                        .attr("x", width/2)
                        .attr("y", height/2)
                        .attr("text-anchor", "middle")
                        .text("Invalid data structure for visualization");
                    console.error("Invalid data:", data);
                    return;
                }}

                // Create a default "name" property if it doesn't exist
                const processNode = (node) => {{
                    if (!node.name && node.title) node.name = node.title;
                    if (!node.name && node.text) node.name = node.text;
                    if (!node.name) node.name = "Unnamed Node";
                    
                    if (node.children && Array.isArray(node.children)) {{
                        node.children.forEach(processNode);
                    }}
                }};
                
                processNode(data);

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
                    .attr("x1", function(d) {{ return d.source.x; }})
                    .attr("y1", function(d) {{ return d.source.y; }})
                    .attr("x2", function(d) {{ return d.target.x; }})
                    .attr("y2", function(d) {{ return d.target.y; }})
                    .attr("stroke", "#999");

                // Nodes
                const nodes = g.selectAll(".node")
                    .data(root.descendants())
                    .enter()
                    .append("g")
                    .attr("class", "node")
                    .attr("transform", function(d) {{ return "translate(" + d.x + "," + d.y + ")"; }});

                nodes.append("circle")
                    .attr("r", 5)
                    .attr("fill", "#69b3a2");

                nodes.append("text")
                    .attr("dy", -10)
                    .attr("x", 6)
                    .text(function(d) {{ 
                        return d.data.name || "Unnamed"; 
                    }});
            </script>
        '''

        # Render HTML with D3.js
        html(html_code, height=700)

    except Exception as e:
        st.error(f"An error occurred: {e}")