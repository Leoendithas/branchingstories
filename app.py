import streamlit as st
from openai import OpenAI
import json
from streamlit.components.v1 import html

# Initialize the OpenAI client correctly
client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

def get_story_json(prompt, is_initial_story=True, branch_length=3, is_alt_ending=False, single_branch=False, include_achievements=True):
    system_message = ""
    if is_initial_story:
        # For the initial story, create a simple linear narrative
        system_message = """You are a storyteller. Create a linear story with a beginning, middle, and end. 
        Respond with valid JSON that represents a simple, linear narrative. 
        
        The JSON should have this structure:
        {
          "name": "Main Story Title",
          "description": "A paragraph describing the overall story theme.",
          "children": [
            {
              "name": "First Story Node",
              "description": "Detailed paragraph about this part of the story.",
              "children": [
                {
                  "name": "Second Story Node",
                  "description": "Next part of the story...",
                  "children": []
                }
              ]
            }
          ]
        }
        
        Create EXACTLY 5 nodes in a linear chain (each one having only ONE child, except the last node).
        Do not include any branching choices at this stage."""
    else:
        # For extending a branch with specific length and merging options
        achievement_instructions = """
        For the FINAL node in each branch, include an 'achievement' object with this structure:
        "achievement": {
          "type": "Achievement",
          "title": "A Creative Achievement Title",
          "description": "Congratulatory message explaining what the student accomplished in this branch."
        }
        
        The achievement title should be catchy and relevant to what happened in this branch.
        The description should be congratulatory and explain what skills or values the student demonstrated.
        """ if include_achievements else ""
        
        if single_branch:
            system_message = f"""You are a branching story generator. 
            Respond with valid JSON that represents a SINGLE new branch for an existing story.
            
            The JSON should have a 'name' field for the node title, a 'description' field with 
            a detailed paragraph, and a 'children' array that will contain the next nodes.
            
            Format:
            {{
              "name": "New Branch Title",
              "description": "Detailed description of what happens in this branch.",
              "children": [
                {{
                  "name": "Next node in the branch",
                  "description": "What happens next in this branch...",
                  "children": []
                }}
              ]
            }}
            
            Create a branch with EXACTLY {branch_length} nodes (including the first node in the branch).
            {'' if is_alt_ending else 'The final node should naturally lead back to the main story.'}
            {' The final node should be an alternative ending with closure.' if is_alt_ending else ''}
            
            {achievement_instructions}
            """
        else:
            system_message = f"""You are a branching story generator. 
            Respond with valid JSON that represents new branches for an existing story.
            
            The JSON should have an array of story options, each with a 'name' field for the node title,
            a 'description' field with a detailed paragraph, and a 'children' array that will contain the next nodes.
            
            Format:
            [
              {{
                "name": "Option 1 Title",
                "description": "Detailed description of what happens in this branch.",
                "children": [
                  {{
                    "name": "Next node in Option l",
                    "description": "What happens next in this branch...",
                    "children": []
                  }}
                ]
              }},
              {{
                "name": "Option 2 Title",
                "description": "Detailed description of what happens in this branch.",
                "children": [
                  {{
                    "name": "Next node in Option 2",
                    "description": "What happens next in this branch...",
                    "children": []
                  }}
                ]
              }}
            ]
            
            Create 2-3 interesting and distinct branching options.
            
            For each option, create a branch with EXACTLY {branch_length} nodes (including the first node in the branch).
            {'' if is_alt_ending else 'The final node should naturally lead back to the main story.'}
            {' The final node should be an alternative ending with closure.' if is_alt_ending else ''}
            
            {achievement_instructions}
            """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7  # Slightly higher temperature for more creative responses
        )
        story_content = response.choices[0].message.content
        
        # Try to clean the response if it's not pure JSON
        if "```json" in story_content or "```" in story_content:
            # Try to extract JSON from the response (if wrapped in ```json or similar)
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', story_content)
            if json_match:
                story_content = json_match.group(1)
        
        # Try to parse the JSON
        return json.loads(story_content)
    
    except (json.JSONDecodeError, Exception) as e:
        st.error(f"Failed to parse JSON response: {e}")
        st.write("Raw response:", story_content)
        
        # Provide a fallback structure
        if is_initial_story:
            return {
                "name": "Student's Day",
                "description": "A day in the life of a student following a linear narrative.",
                "children": [
                    {
                        "name": "Morning Begins",
                        "description": "The student starts their day with their morning routine.",
                        "children": [
                            {
                                "name": "Heading to School",
                                "description": "After getting ready, the student heads to school.",
                                "children": [
                                    {
                                        "name": "First Class",
                                        "description": "The student attends their first class of the day.",
                                        "children": [
                                            {
                                                "name": "End of Day",
                                                "description": "The student completes their day and heads home.",
                                                "children": []
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        else:
            # Default branching structure
            branch_nodes = []
            for i in range(branch_length - 1):
                if i == branch_length - 2:  # Last node in the branch
                    branch_nodes.append({
                        "name": f"Final Node in Branch",
                        "description": "The conclusion of this branch of the story.",
                        "children": []
                    })
                else:
                    branch_nodes.append({
                        "name": f"Node {i+2} in Branch",
                        "description": f"Continuing the story in this branch...",
                        "children": [branch_nodes[-1]] if branch_nodes else []
                    })
            
            return [
                {
                    "name": "Option A",
                    "description": "This is the first possible branch of the story.",
                    "children": [branch_nodes[0]] if branch_nodes else []
                },
                {
                    "name": "Option B",
                    "description": "This is the second possible branch of the story.",
                    "children": [branch_nodes[0]] if branch_nodes else []
                }
            ]

# Streamlit UI setup
st.title('Branching Story Visualizer')

# Create two columns for story generation
col1, col2 = st.columns([1, 1])

with col1:
    # Main story prompt
    prompt = st.text_area('Enter your prompt for the main storyline:',
                        "Create a story about a student's day at school.")
    
    st.markdown("*Note: This will create a linear story with no branches. You can add branches later.*")
    
    generate_button = st.button('Generate Story')

# Place to store our story data
if 'story_data' not in st.session_state:
    st.session_state.story_data = None

# Handle story generation
if generate_button:
    with st.spinner('Generating story...'):
        st.session_state.story_data = get_story_json(prompt, is_initial_story=True)

# Render visualization if we have data
if st.session_state.story_data:
    # Create visualization
    with col2:
        st.subheader("Story Structure")
        st.write("Click on nodes to view details")
    
    # Create D3.js visualization HTML - using string concatenation instead of f-strings for JavaScript
    visualization_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            #story-container {
                display: flex;
                width: 100%;
                height: 600px;
            }
            #tree-container {
                flex: 2;
                height: 550px;
                overflow: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 10px;
            }
            #detail-panel {
                flex: 1;
                padding: 15px;
                background-color: #f5f7f9;
                border-left: 1px solid #ddd;
                margin-left: 10px;
                border-radius: 5px;
                overflow: auto;
            }
            .node circle {
                fill: #69b3a2;
                stroke: #3a7759;
                stroke-width: 1.5px;
            }
            .node text {
                font: 12px sans-serif;
                fill: #333;
            }
            .node:hover circle {
                fill: #3a7759;
            }
            .link {
                fill: none;
                stroke: #ccc;
                stroke-width: 2px;
            }
            .selected-node circle {
                fill: #ff7f0e;
                stroke: #d26013;
                stroke-width: 2px;
            }
            .merge-node circle {
                fill: #9370DB;
                stroke: #4B0082;
                stroke-width: 2px;
            }
            .achievement-node circle {
                fill: #FFD700;
                stroke: #DAA520;
                stroke-width: 2px;
            }
            .merge-link {
                fill: none;
                stroke: #9370DB;
                stroke-width: 2px;
                stroke-dasharray: 5,5;
            }
            h3 {
                margin-top: 5px;
                color: #333;
            }
            .achievement-badge {
                background-color: #FFF8DC;
                border: 2px solid #FFD700;
                border-radius: 8px;
                padding: 10px;
                margin-top: 15px;
            }
            .achievement-badge h4 {
                color: #DAA520;
                margin-top: 0;
                margin-bottom: 5px;
            }
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
            const data = ''' + json.dumps(st.session_state.story_data) + ''';
            
            // Process nodes to ensure they have proper properties
            function processNode(node) {
                if (!node.name) node.name = node.title || "Unnamed Node";
                if (!node.description) node.description = node.text || "";
                
                if (node.children && Array.isArray(node.children)) {
                    node.children.forEach(processNode);
                }
                return node;
            }
            
            const processedData = processNode(JSON.parse(JSON.stringify(data)));
            
            // Set up tree visualization with vertical layout
            const margin = {top: 50, right: 30, bottom: 50, left: 50};
            const width = document.getElementById('tree-container').clientWidth - margin.left - margin.right;
            const height = document.getElementById('tree-container').clientHeight - margin.top - margin.bottom;
            
            // Create SVG
            const svg = d3.select("#tree-container").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + (width/2) + "," + margin.top + ")")
                .call(d3.zoom().on("zoom", function(event) {
                    svg.attr("transform", event.transform);
                }));
            
            // Add arrowhead definitions to SVG
            svg.append("defs").selectAll("marker")
                .data(["arrow", "merge-arrow"])
                .enter().append("marker")
                .attr("id", function(d) { return d; })
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 10)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", function(d) { return d === "merge-arrow" ? "#9370DB" : "#999"; });
                
            // Create tree layout - vertical orientation (top to bottom)
            const root = d3.hierarchy(processedData);
            const nodeCount = root.descendants().length;
            
            // Create a Y-axis spacing variable based on the number of nodes
            const ySpacing = Math.min(120, (height * 0.8) / (nodeCount + 1));
            
            // Create tree layout - vertical orientation (top to bottom)
            const treeLayout = d3.tree()
                .size([width * 0.7, nodeCount <= 5 ? height * 0.7 : height * 0.85]) // Adaptive sizing
                .nodeSize([0, ySpacing]) // Set consistent vertical spacing between nodes
                .separation(function(a, b) { return 3; }); // Increase horizontal separation
            
            // Apply the layout
            treeLayout(root);
            
            // Store merge nodes and their targets for later processing
            const mergeNodes = [];
            
            // Post-process node positions for branches
            root.descendants().forEach(function(d) {
                // Collect merge nodes
                if (d.data.merge_target) {
                    mergeNodes.push({
                        node: d,
                        targetPath: d.data.merge_target
                    });
                }
                
                // For nodes with multiple children (branching points)
                if (d.children && d.children.length > 1) {
                    // Calculate the width needed for the branches
                    const branchWidth = d.children.length * 80;
                    
                    // Adjust positions of child nodes
                    d.children.forEach(function(child, i) {
                        const offset = branchWidth * (i / (d.children.length - 1) - 0.5);
                        child.x = d.x + offset;
                        
                        // Recursively adjust positions of all descendants
                        function adjustDescendants(node) {
                            if (node.children) {
                                node.children.forEach(function(c) {
                                    c.x += offset;
                                    adjustDescendants(c);
                                });
                            }
                        }
                        adjustDescendants(child);
                    });
                }
            });
            
            // Add links - using curved lines for better visualization
            const link = svg.selectAll(".link")
                .data(root.links())
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", function(d) {
                    // Create a gentle curve for the links
                    return "M" + d.source.x + "," + d.source.y +
                           "C" + d.source.x + "," + (d.source.y + 50) +
                           " " + d.target.x + "," + (d.target.y - 50) +
                           " " + d.target.x + "," + d.target.y;
                })
                .attr("marker-end", "url(#arrow)");
            
            // Create node groups
            const node = svg.selectAll(".node")
                .data(root.descendants())
                .enter()
                .append("g")
                .attr("class", function(d) { 
                    let classNames = "node";
                    classNames += d.children ? " node--internal" : " node--leaf";
                    if (d.data.merge_target) classNames += " merge-node";
                    if (d.data.achievement) classNames += " achievement-node";
                    return classNames;
                })
                .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
                .on("click", function(event, d) {
                    // Remove previous selection
                    d3.selectAll(".selected-node").classed("selected-node", false);
                    
                    // Add selection to clicked node
                    d3.select(this).classed("selected-node", true);
                    
                    // Update detail panel
                    showNodeDetails(d.data);
                });
            
            // Add circles to nodes
            node.append("circle")
                .attr("r", 5);
            
            // Add text labels with background rectangles for better readability
            node.append("text")
                .attr("dy", -20) // Move text higher above the node
                .attr("x", 0)
                .attr("text-anchor", "middle")
                .text(function(d) { 
                    // Truncate long node names to prevent overlap
                    const name = d.data.name;
                    return name.length > 20 ? name.substring(0, 18) + "..." : name;
                })
                .each(function(d) {
                    // Add background rectangle for text
                    const bbox = this.getBBox();
                    const padding = 3;
                    
                    d3.select(this.parentNode).insert("rect", "text")
                        .attr("x", bbox.x - padding)
                        .attr("y", bbox.y - padding)
                        .attr("width", bbox.width + (padding * 2))
                        .attr("height", bbox.height + (padding * 2))
                        .attr("fill", d.data.achievement ? "#FFF8DC" : d.data.merge_target ? "#F0E6FF" : "white")
                        .attr("fill-opacity", 0.8)
                        .attr("rx", 3)
                        .attr("ry", 3);
                });
            
            // Function to find a node by path
            function findNodeByPath(root, path) {
                let current = root;
                for (let i = 0; i < path.length; i++) {
                    if (!current.children || path[i] >= current.children.length) {
                        return null;
                    }
                    current = current.children[path[i]];
                }
                return current;
            }
            
            // Add visual merge connections
            if (mergeNodes.length > 0) {
                // For each merge node, find its target and create a visual connection
                mergeNodes.forEach(function(mergeInfo) {
                    const sourceNode = mergeInfo.node;
                    const targetNode = findNodeByPath(root, mergeInfo.targetPath);
                    
                    if (targetNode) {
                        // Add a dashed line connecting to the merge target
                        svg.append("path")
                            .attr("class", "merge-link")
                            .attr("d", function() {
                                // Create a curved line from merge node to target
                                return "M" + sourceNode.x + "," + sourceNode.y +
                                       "C" + sourceNode.x + "," + (sourceNode.y + 100) +
                                       " " + targetNode.x + "," + (targetNode.y - 100) +
                                       " " + targetNode.x + "," + targetNode.y;
                            })
                            .attr("marker-end", "url(#merge-arrow)");
                    }
                });
            }
            
            // Function to show node details
            function showNodeDetails(nodeData) {
                const detailsDiv = document.getElementById('node-details');
                
                // Create HTML content
                let content = "<h4>" + (nodeData.name || 'Unnamed Node') + "</h4>" +
                              "<p>" + (nodeData.description || 'No description available.') + "</p>";
                
                // Show achievement if it exists
                if (nodeData.achievement) {
                    content += '<div class="achievement-badge">' +
                               '<h4>🏆 ' + nodeData.achievement.title + '</h4>' +
                               '<p>' + nodeData.achievement.description + '</p>' +
                               '</div>';
                }
                
                if (nodeData.merge_target) {
                    content += "<p><em>This node merges back to the main storyline.</em></p>";
                } else if (nodeData.children && nodeData.children.length > 0) {
                    content += "<p><strong>Options:</strong></p><ul>";
                    nodeData.children.forEach(function(child) {
                        content += "<li>" + child.name + "</li>";
                    });
                    content += "</ul>";
                } else {
                    content += "<p><em>This is an endpoint of the story.</em></p>";
                }
                
                detailsDiv.innerHTML = content;
            }
            
            // Select the root node initially
            node.filter(function(d) { return !d.parent; })
                .classed("selected-node", true)
                .each(function(d) { showNodeDetails(d.data); });
        </script>
    </body>
    </html>
    '''
            
            // Apply the layout
            treeLayout(root);
            
            // Store merge nodes and their targets for later processing
            const mergeNodes = [];
            
            // Post-process node positions for branches
            root.descendants().forEach(function(d) {
                // Collect merge nodes
                if (d.data.merge_target) {
                    mergeNodes.push({
                        node: d,
                        targetPath: d.data.merge_target
                    });
                }
                
                // For nodes with multiple children (branching points)
                if (d.children && d.children.length > 1) {
                    // Calculate the width needed for the branches
                    const branchWidth = d.children.length * 80;
                    
                    // Adjust positions of child nodes
                    d.children.forEach(function(child, i) {
                        const offset = branchWidth * (i / (d.children.length - 1) - 0.5);
                        child.x = d.x + offset;
                        
                        // Recursively adjust positions of all descendants
                        function adjustDescendants(node) {
                            if (node.children) {
                                node.children.forEach(function(c) {
                                    c.x += offset;
                                    adjustDescendants(c);
                                });
                            }
                        }
                        adjustDescendants(child);
                    });
                }
            });
            
            // Add links - using curved lines for better visualization
            const link = svg.selectAll(".link")
                .data(root.links())
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", function(d) {
                    // Create a gentle curve for the links
                    return "M" + d.source.x + "," + d.source.y +
                           "C" + d.source.x + "," + (d.source.y + 50) +
                           " " + d.target.x + "," + (d.target.y - 50) +
                           " " + d.target.x + "," + d.target.y;
                })
                .attr("marker-end", "url(#arrow)");
            
            // Create node groups
            const node = svg.selectAll(".node")
                .data(root.descendants())
                .enter()
                .append("g")
                .attr("class", function(d) { 
                    let classNames = "node";
                    classNames += d.children ? " node--internal" : " node--leaf";
                    if (d.data.merge_target) classNames += " merge-node";
                    return classNames;
                })
                .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
                .on("click", function(event, d) {
                    // Remove previous selection
                    d3.selectAll(".selected-node").classed("selected-node", false);
                    
                    // Add selection to clicked node
                    d3.select(this).classed("selected-node", true);
                    
                    // Update detail panel
                    showNodeDetails(d.data);
                });
            
            // Add circles to nodes
            node.append("circle")
                .attr("r", 5);
            
            // Add text labels with background rectangles for better readability
            node.append("text")
                .attr("dy", -20) // Move text higher above the node
                .attr("x", 0)
                .attr("text-anchor", "middle")
                .text(function(d) { 
                    // Truncate long node names to prevent overlap
                    const name = d.data.name;
                    return name.length > 20 ? name.substring(0, 18) + "..." : name;
                })
                .each(function(d) {
                    // Add background rectangle for text
                    const bbox = this.getBBox();
                    const padding = 3;
                    
                    d3.select(this.parentNode).insert("rect", "text")
                        .attr("x", bbox.x - padding)
                        .attr("y", bbox.y - padding)
                        .attr("width", bbox.width + (padding * 2))
                        .attr("height", bbox.height + (padding * 2))
                        .attr("fill", d.data.merge_target ? "#F0E6FF" : "white")
                        .attr("fill-opacity", 0.8)
                        .attr("rx", 3)
                        .attr("ry", 3);
                });
            
            // Function to find a node by path
            function findNodeByPath(root, path) {
                let current = root;
                for (let i = 0; i < path.length; i++) {
                    if (!current.children || path[i] >= current.children.length) {
                        return null;
                    }
                    current = current.children[path[i]];
                }
                return current;
            }
            
            // Add visual merge connections
            if (mergeNodes.length > 0) {
                // For each merge node, find its target and create a visual connection
                mergeNodes.forEach(function(mergeInfo) {
                    const sourceNode = mergeInfo.node;
                    const targetNode = findNodeByPath(root, mergeInfo.targetPath);
                    
                    if (targetNode) {
                        // Add a dashed line connecting to the merge target
                        svg.append("path")
                            .attr("class", "merge-link")
                            .attr("d", function() {
                                // Create a curved line from merge node to target
                                return "M" + sourceNode.x + "," + sourceNode.y +
                                       "C" + sourceNode.x + "," + (sourceNode.y + 100) +
                                       " " + targetNode.x + "," + (targetNode.y - 100) +
                                       " " + targetNode.x + "," + targetNode.y;
                            })
                            .attr("marker-end", "url(#merge-arrow)");
                    }
                });
            }
            
            // Function to show node details
            function showNodeDetails(nodeData) {
                const detailsDiv = document.getElementById('node-details');
                
                // Create HTML content
                let content = "<h4>" + (nodeData.name || 'Unnamed Node') + "</h4>" +
                              "<p>" + (nodeData.description || 'No description available.') + "</p>";
                
                if (nodeData.merge_target) {
                    content += "<p><em>This node merges back to the main storyline.</em></p>";
                } else if (nodeData.children && nodeData.children.length > 0) {
                    content += "<p><strong>Options:</strong></p><ul>";
                    nodeData.children.forEach(function(child) {
                        content += "<li>" + child.name + "</li>";
                    });
                    content += "</ul>";
                } else {
                    content += "<p><em>This is an endpoint of the story.</em></p>";
                }
                
                detailsDiv.innerHTML = content;
            }
            
            // Select the root node initially
            node.filter(function(d) { return !d.parent; })
                .classed("selected-node", true)
                .each(function(d) { showNodeDetails(d.data); });
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
    
    # Store path information for each node to find it later
    if 'node_paths' not in st.session_state:
        st.session_state.node_paths = {}
    
    # Function to recursively extract node names with paths
    def extract_node_paths(node, path=None, prefix=""):
        if path is None:
            path = []
        
        result = []
        current_path = path.copy()
        name = prefix + node.get("name", "Unnamed")
        
        # Store the full path to this node
        st.session_state.node_paths[name] = current_path
        
        result.append(name)
        
        for i, child in enumerate(node.get("children", [])):
            child_path = current_path.copy()
            child_path.append(i)
            child_results = extract_node_paths(child, child_path, prefix + "→ ")
            result.extend(child_results)
            
        return result
    
    # Find a node using the stored path
    def get_node_by_path(root, path):
        node = root
        for index in path:
            if index < len(node.get("children", [])):
                node = node["children"][index]
            else:
                return None
        return node
    
    # Get all node names with their paths
    node_options = ["Select a node to extend..."]
    if st.session_state.story_data:
        st.session_state.node_paths = {}  # Reset paths
        node_options.extend(extract_node_paths(st.session_state.story_data))
    
    # Create two columns for branch source and destination
    branch_col1, branch_col2 = st.columns(2)
    
    with branch_col1:
        source_node = st.selectbox("Branch from node:", node_options, key="source_node")
    
    with branch_col2:
        # Add an option for alternative ending (no merging)
        merge_options = ["Alternative Ending (No Merge)"] + node_options
        dest_node = st.selectbox("Merge to node (or choose alternative ending):", 
                                merge_options, key="dest_node")
    
    # Branch length slider
    branch_length = st.slider("Number of nodes in branch path:", min_value=2, max_value=10, value=3)
    
    # Add a toggle for achievements
    achievements_enabled = st.checkbox("Enable achievements at branch endings", value=True,
                                     help="When enabled, students will receive achievements upon completing branches")
    
    # Add a radio button for single branch vs multiple branches
    branch_type = st.radio(
        "Branch creation mode:",
        ["Create single branch", "Create multiple branches (2-3 options)"],
        index=0
    )
    
    single_branch_mode = branch_type == "Create single branch"
    
    # Only show extension options if a real source node is selected
    if source_node != "Select a node to extend...":
        # Get context for the selected source node to help the AI generate relevant branches
        source_node_context = ""
        dest_node_context = ""
        
        if source_node in st.session_state.node_paths:
            source_path = st.session_state.node_paths[source_node]
            source_node_obj = get_node_by_path(st.session_state.story_data, source_path)
            if source_node_obj:
                source_node_context = f"Source node: {source_node_obj.get('name')}\nDescription: {source_node_obj.get('description')}"
        
        if dest_node != "Alternative Ending (No Merge)" and dest_node != "Select a node to extend...":
            if dest_node in st.session_state.node_paths:
                dest_path = st.session_state.node_paths[dest_node]
                dest_node_obj = get_node_by_path(st.session_state.story_data, dest_path)
                if dest_node_obj:
                    dest_node_context = f"Destination node: {dest_node_obj.get('name')}\nDescription: {dest_node_obj.get('description')}"
        
        is_alt_ending = dest_node == "Alternative Ending (No Merge)"
        
        if single_branch_mode:
            branch_label = "branch"
            extension_prompt_default = f"Create a branch from '{source_node.split('→ ')[-1]}'" + \
                (f" that eventually leads to '{dest_node.split('→ ')[-1]}'" if not is_alt_ending and dest_node != "Select a node to extend..." else 
                " with an alternative ending")
        else:
            branch_label = "branches"
            extension_prompt_default = f"Create branches from '{source_node.split('→ ')[-1]}'" + \
                (f" that eventually lead to '{dest_node.split('→ ')[-1]}'" if not is_alt_ending and dest_node != "Select a node to extend..." else 
                " with alternative endings")
        
        extension_prompt = st.text_area(
            f"How would you like to extend this {branch_label}?", 
            extension_prompt_default
        )
        
        if st.button(f"Create {branch_label.capitalize()}"):
            with st.spinner(f'Generating {branch_label}...'):
                # Create the full context for the API call
                full_prompt = f"""
                {source_node_context}
                
                {dest_node_context if dest_node_context else ""}
                
                {extension_prompt}
                
                {"Create an alternative ending that provides closure to the story." if is_alt_ending else 
                 f"Create a branch that naturally leads to the destination node after {branch_length} steps." if dest_node != "Select a node to extend..." else ""}
                """
                
                # Get branch options from the API
                branch_options = get_story_json(full_prompt, 
                                               is_initial_story=False, 
                                               branch_length=branch_length,
                                               is_alt_ending=is_alt_ending,
                                               single_branch=single_branch_mode)
                
                # If single branch mode was used, we need to wrap the result in an array
                if single_branch_mode and not isinstance(branch_options, list):
                    branch_options = [branch_options]
                # Find the source node to extend
                if source_node in st.session_state.node_paths:
                    source_path = st.session_state.node_paths[source_node]
                    
                    # For merging, we need to eventually connect to the destination node
                    if not is_alt_ending and dest_node != "Select a node to extend...":
                        if dest_node in st.session_state.node_paths:
                            dest_path = st.session_state.node_paths[dest_node]
                            dest_node_obj = get_node_by_path(st.session_state.story_data, dest_path)
                            
                            # Create a deeper copy for branch options to avoid reference issues
                            import copy
                            branch_options_copy = copy.deepcopy(branch_options)
                            
                # For each branch option, find the last node in the chain
                for branch in branch_options_copy:
                    # Navigate to the last node in the branch
                    current_node = branch
                    previous_node = None
                    depth = 0
                    
                    # Navigate to the last node but stop before we reach the maximum depth
                    while current_node.get("children", []) and depth < branch_length - 2:
                        if not current_node["children"]:
                            break
                        previous_node = current_node
                        current_node = current_node["children"][0]
                        depth += 1
                    
                    # Instead of directly connecting to the destination node object,
                    # create a special node that references the destination but avoids circular references
                    if dest_node_obj:
                        # Before creating merge node, check if this node needs an achievement
                        # Ensure achievement exists if this is the final node in the branch
                        if "achievement" not in current_node and not is_alt_ending:
                            current_node["achievement"] = {
                                "type": "Achievement",
                                "title": f"Completed: {current_node.get('name', 'Branch')}",
                                "description": f"Congratulations! You completed the '{current_node.get('name', 'branch')}' storyline and demonstrated excellent decision-making skills."
                            }
                        
                        # Create a pointer node instead of directly using the dest_node_obj
                        merge_node = {
                            "name": f"Merge back to: {dest_node_obj.get('name', 'Destination')}",
                            "description": f"This path merges back to the main storyline at '{dest_node_obj.get('name', 'Destination')}'.",
                            "children": [],
                            "merge_target": dest_path  # Store just the path to the target, not the object itself
                        }
                        current_node["children"] = [merge_node]
                    elif is_alt_ending:
                        # If this is an alternate ending, make sure it has an achievement
                        if "achievement" not in current_node:
                            current_node["achievement"] = {
                                "type": "Achievement",
                                "title": f"Alternate Ending: {current_node.get('name', 'Conclusion')}",
                                "description": f"Congratulations! You've discovered an alternate ending to the story. Your unique choices led to this special conclusion."
                            }
                            
                            branch_options = branch_options_copy
                    
                    # Helper function to update the story tree
                    def update_node_children(node, path, index, new_children):
                        if index >= len(path):
                            # We've reached the target node, APPEND new children instead of replacing
                            if "children" not in node:
                                node["children"] = []
                            
                            # Append the new branches
                            node["children"] = node.get("children", []) + new_children
                            return True
                        
                        if "children" not in node or index >= len(path) or path[index] >= len(node["children"]):
                            return False
                        
                        # Continue traversing
                        return update_node_children(node["children"][path[index]], path, index + 1, new_children)
                    
                    # Update the story tree
                    success = update_node_children(st.session_state.story_data, source_path, 0, branch_options)
                    
                    if success:
                        # Get the node that was updated
                        updated_node = get_node_by_path(st.session_state.story_data, source_path)
                        branch_count = len(updated_node.get("children", []))
                        original_count = branch_count - len(branch_options)
                        
                        merge_message = ""
                        if not is_alt_ending and dest_node != "Select a node to extend...":
                            merge_message = f" They will merge back to '{dest_node.split('→ ')[-1]}' after {branch_length} steps."
                        elif is_alt_ending:
                            merge_message = f" They will create alternative endings after {branch_length} steps."
                        
                        if original_count > 0:
                            message = f"Successfully added {len(branch_options)} new branches to the story while preserving the original {original_count} path(s)!{merge_message}"
                        else:
                            message = f"Successfully added {len(branch_options)} new branches to the story!{merge_message}"
                        
                        st.success(message)
                        # Force a rerun to update the visualization
                        st.rerun()
                    else:
                        st.error("Failed to update the story structure. Please try again.")