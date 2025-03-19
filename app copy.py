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
        
        # Create a complete HTML document for D3.js visualization
        html_code = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Branching Story Visualization</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                #d3-container {{
                    width: 100%;
                    height: 600px;
                    overflow: auto;
                }}
                .link {{
                    stroke: #999;
                    stroke-width: 1.5px;
                }}
                .node circle {{
                    fill: #69b3a2;
                    stroke: #3a7759;
                    stroke-width: 1.5px;
                }}
                .node text {{
                    font: 12px sans-serif;
                }}
            </style>
        </head>
        <body>
            <div id="d3-container"></div>
            <script>
                // Data from Python
                const data = {json.dumps(story_data)};
                console.log("Data received in D3:", data);
                
                document.addEventListener('DOMContentLoaded', function() {{
                    // Get container dimensions
                    const containerWidth = document.getElementById('d3-container').clientWidth;
                    const width = containerWidth || 800;
                    const height = 600;
                    
                    const svg = d3.select("#d3-container").append("svg")
                        .attr("width", width)
                        .attr("height", height)
                        .append("g")
                        .attr("transform", "translate(40,20)");
                    
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
                    
                    // Process nodes to ensure they have name properties
                    const processNode = (node) => {{
                        if (!node.name && node.title) node.name = node.title;
                        if (!node.name && node.text) node.name = node.text;
                        if (!node.name) node.name = "Unnamed Node";
                        
                        if (node.children && Array.isArray(node.children)) {{
                            node.children.forEach(processNode);
                        }}
                        return node;
                    }};
                    
                    const processedData = processNode(JSON.parse(JSON.stringify(data)));
                    
                    try {{
                        // Create the tree layout
                        const root = d3.hierarchy(processedData);
                        const treeLayout = d3.tree().size([height - 40, width - 160]);
                        
                        // This will position nodes
                        const nodes = treeLayout(root);
                        
                        // Add links between nodes
                        svg.selectAll(".link")
                            .data(nodes.links())
                            .enter()
                            .append("path")
                            .attr("class", "link")
                            .attr("d", d3.linkHorizontal()
                                .x(d => d.y)  // Swap x and y for horizontal layout
                                .y(d => d.x)
                            );
                        
                        // Add nodes
                        const node = svg.selectAll(".node")
                            .data(nodes.descendants())
                            .enter()
                            .append("g")
                            .attr("class", "node")
                            .attr("transform", d => `translate(${{d.y}},${{d.x}})`);
                        
                        // Add circles to nodes
                        node.append("circle")
                            .attr("r", 6);
                        
                        // Add labels to nodes
                        node.append("text")
                            .attr("dy", 3)
                            .attr("x", d => d.children ? -8 : 8)
                            .style("text-anchor", d => d.children ? "end" : "start")
                            .text(d => d.data.name);
                            
                        console.log("Visualization completed");
                    }} catch (error) {{
                        console.error("Error rendering visualization:", error);
                        svg.append("text")
                            .attr("x", width/2)
                            .attr("y", height/2)
                            .attr("text-anchor", "middle")
                            .text("Error rendering visualization: " + error.message);
                    }}
                }});
            </script>
        </body>
        </html>
        '''

        # Render HTML with D3.js
        # Increase the height and add scrolling to ensure the visualization is visible
        html(html_code, height=700, scrolling=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")