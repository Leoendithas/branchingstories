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
            {"role": "system", "content": "You are a branching story generator. Always respond with valid JSON that represents a tree structure for a branching story. The JSON should have a 'name' field for the node title, a 'description' field for a short paragraph about this node, and a 'children' array for branching options."},
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
            "name": "Student",
            "description": "A day in the life of a student begins with a choice.",
            "children": [
                {
                    "name": "Wake Up Early",
                    "description": "You decide to wake up early and start your day with plenty of time.",
                    "children": []
                },
                {
                    "name": "Wake Up Late",
                    "description": "You hit the snooze button too many times and now you're running late.",
                    "children": []
                }
            ]
        }

# Streamlit UI setup
st.title('Branching Story Visualizer')

# Create two columns for story generation
col1, col2 = st.columns([1, 1])

with col1:
    # Main story prompt
    prompt = st.text_area('Enter your prompt for the main storyline:',
                        "Create a branching story about a student's day at school with initial choices.")
    
    generate_button = st.button('Generate Story')

# Place to store our story data
if 'story_data' not in st.session_state:
    st.session_state.story_data = None

# Handle story generation
if generate_button:
    with st.spinner('Generating story...'):
        st.session_state.story_data = get_story_json(prompt)

# Render visualization if we have data
if st.session_state.story_data:
    # Create visualization
    with col2:
        st.subheader("Story Structure")
        st.write("Click on nodes to view details")
    
    # D3.js visualization with node details panel
    visualization_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            #story-container {{
                display: flex;
                width: 100%;
                height: 600px;
            }}
            #tree-container {{
                flex: 2;
                overflow: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }}
            #detail-panel {{
                flex: 1;
                padding: 15px;
                background-color: #f5f7f9;
                border-left: 1px solid #ddd;
                margin-left: 10px;
                border-radius: 5px;
                overflow: auto;
            }}
            .node circle {{
                fill: #69b3a2;
                stroke: #3a7759;
                stroke-width: 1.5px;
            }}
            .node text {{
                font: 12px sans-serif;
                fill: #333;
            }}
            .node:hover circle {{
                fill: #3a7759;
            }}
            .link {{
                fill: none;
                stroke: #ccc;
                stroke-width: 2px;
            }}
            .selected-node circle {{
                fill: #ff7f0e;
                stroke: #d26013;
                stroke-width: 2px;
            }}
            h3 {{
                margin-top: 5px;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div id="story-container">
            <div id="tree-container"></div>
            <div id="detail-panel">
                <h3>Node Details</h3>
                <p>Click on a node to view its details.</p>
                <div id="node-details"></div>
            </div>
        </div>

        <script src="https://d3js.org/d3.v7.min.js"></script>
        <script>
            // Data from Python
            const data = {json.dumps(st.session_state.story_data)};
            
            // Process nodes to ensure they have proper properties
            function processNode(node) {{
                if (!node.name) node.name = node.title || "Unnamed Node";
                if (!node.description) node.description = node.text || "";
                
                if (node.children && Array.isArray(node.children)) {{
                    node.children.forEach(processNode);
                }}
                return node;
            }}
            
            const processedData = processNode(JSON.parse(JSON.stringify(data)));
            
            // Set up tree visualization
            const margin = {{top: 30, right: 30, bottom: 30, left: 50}};
            const width = document.getElementById('tree-container').clientWidth - margin.left - margin.right;
            const height = document.getElementById('tree-container').clientHeight - margin.top - margin.bottom;
            
            // Create SVG
            const svg = d3.select("#tree-container").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
            
            // Create tree layout
            const root = d3.hierarchy(processedData);
            
            // Count nodes to determine layout size
            const nodeCount = root.descendants().length;
            
            // Create horizontal tree layout
            const treeLayout = d3.tree()
                .size([height, width - 200]);  // Make more horizontal space for the diagram
            
            // Apply the layout
            treeLayout(root);
            
            // Add links
            const link = svg.selectAll(".link")
                .data(root.links())
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x)
                );
            
            // Create node groups
            const node = svg.selectAll(".node")
                .data(root.descendants())
                .enter()
                .append("g")
                .attr("class", d => "node" + (d.children ? " node--internal" : " node--leaf"))
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`)
                .on("click", function(event, d) {{
                    // Remove previous selection
                    d3.selectAll(".selected-node").classed("selected-node", false);
                    
                    // Add selection to clicked node
                    d3.select(this).classed("selected-node", true);
                    
                    // Update detail panel
                    showNodeDetails(d.data);
                }});
            
            // Add circles to nodes
            node.append("circle")
                .attr("r", 5);
            
            // Add text labels, with proper positioning and background for readability
            node.append("text")
                .attr("dy", 3)
                .attr("x", d => d.children ? -10 : 10)
                .attr("text-anchor", d => d.children ? "end" : "start")
                .text(d => d.data.name)
                .each(function(d) {{
                    // Add background rectangle for text
                    const bbox = this.getBBox();
                    const padding = 2;
                    
                    d3.select(this.parentNode).insert("rect", "text")
                        .attr("x", bbox.x - padding)
                        .attr("y", bbox.y - padding)
                        .attr("width", bbox.width + (padding * 2))
                        .attr("height", bbox.height + (padding * 2))
                        .attr("fill", "white")
                        .attr("fill-opacity", 0.8);
                }});
            
            // Function to show node details
            function showNodeDetails(nodeData) {{
                const detailsDiv = document.getElementById('node-details');
                
                // Create HTML content
                let content = `
                    <h4>${{nodeData.name || 'Unnamed Node'}}</h4>
                    <p>${{nodeData.description || 'No description available.'}}</p>
                `;
                
                if (nodeData.children && nodeData.children.length > 0) {{
                    content += `<p><strong>Options:</strong></p><ul>`;
                    nodeData.children.forEach(child => {{
                        content += `<li>${{child.name}}</li>`;
                    }});
                    content += `</ul>`;
                }} else {{
                    content += `<p><em>This is an endpoint of the story.</em></p>`;
                }}
                
                detailsDiv.innerHTML = content;
            }}
            
            // Select the root node initially
            node.filter(d => !d.parent)
                .classed("selected-node", true)
                .each(d => showNodeDetails(d.data));
        </script>
    </body>
    </html>
    '''
    
    # Display visualization immediately after the Generate button
    st.markdown("---")  # Divider
    html(visualization_html, height=650, scrolling=True)
    
    # Add a section for extending the story
    st.markdown("---")
    st.subheader("Extend The Story")
    
    # Choose a node to extend
    node_options = ["Select a node to extend..."]
    
    # Function to recursively extract node names (simplified)
    def extract_node_names(node, prefix=""):
        result = []
        name = prefix + node.get("name", "Unnamed")
        result.append(name)
        for child in node.get("children", []):
            result.extend(extract_node_names(child, prefix + "→ "))
        return result
    
    # Get all node names
    if st.session_state.story_data:
        node_options.extend(extract_node_names(st.session_state.story_data))
    
    selected_node = st.selectbox("Select a node to extend:", node_options)
    
    # Only show extension options if a real node is selected
    if selected_node != "Select a node to extend...":
        extension_prompt = st.text_area(
            "How would you like to extend this branch?", 
            "Add 2 new choices for what happens after this point in the story."
        )
        
        if st.button("Extend Branch"):
            st.write("This would extend the selected branch with new options.")
            # This is where you would implement the branch extension logic