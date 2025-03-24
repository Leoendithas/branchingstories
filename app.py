import streamlit as st
from openai import OpenAI
import json
from streamlit.components.v1 import html

# Initialize the OpenAI client correctly
client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

def get_story_json(prompt, is_initial_story=True, is_merge_branch=False, merge_target_id=None):
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
    elif is_merge_branch:
        # For creating a merge branch that connects back to the main story
        system_message = f"""You are a storyteller creating a branch that will merge back into the main story.
        Respond with valid JSON that represents a connecting narrative path.
        
        The JSON should have this structure:
        {{
          "name": "Merge Branch Title",
          "description": "Detailed paragraph about this part of the story that will logically lead back to the main story.",
          "is_merge_point": true,
          "merge_target_id": "{merge_target_id}",
          "children": []
        }}
        
        Create a logical transition that explains how the character or plot returns to the main storyline.
        The merge_target_id field has been pre-filled with the correct target node ID."""
    else:
        # For extending a branch, create multiple choices
        system_message = """You are a branching story generator. 
        Respond with valid JSON that represents new branches for an existing story.
        
        The JSON should have an array of story options, each with a 'name' field for the node title,
        a 'description' field with a detailed paragraph, and an empty 'children' array.
        
        Format:
        [
          {
            "name": "Option 1 Title",
            "description": "Detailed description of what happens in this branch.",
            "children": []
          },
          {
            "name": "Option 2 Title",
            "description": "Detailed description of what happens in this branch.",
            "children": []
          }
        ]
        
        Create 2-3 interesting and distinct branching options."""
    
    try:
        # Create verbose debugging for JSON parsing
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7  # Slightly higher temperature for more creative responses
            )
            story_content = response.choices[0].message.content
            
            # Debug the raw response
            print("Raw LLM response:", story_content)
            
            # Try to clean the response if it's not pure JSON
            if "```json" in story_content or "```" in story_content:
                # Try to extract JSON from the response (if wrapped in ```json or similar)
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', story_content)
                if json_match:
                    story_content = json_match.group(1)
                    print("Extracted JSON from code block:", story_content)
            
            # Try to parse the JSON
            parsed_json = json.loads(story_content)
            print("Successfully parsed JSON")
            return parsed_json
            
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            print(f"Content that failed to parse: {story_content}")
            raise
        except Exception as api_error:
            print(f"API or processing error: {api_error}")
            raise
    
    except (json.JSONDecodeError, Exception) as e:
        st.error(f"Failed to parse JSON response: {e}")
        if isinstance(e, json.JSONDecodeError):
            st.write("Raw response that failed to parse:")
            st.code(story_content, language="json")
        
        # Provide a fallback structure
        if is_initial_story:
            fallback = {
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
            st.info("Used fallback story structure.")
            return fallback
                            elif is_merge_branch:
            fallback = {
                "name": "Return to Main Story",
                "description": "This branch converges back to the main storyline.",
                "is_merge_point": True,
                "merge_target_id": merge_target_id or "node_3", # Use provided target or default
                "children": []
            }
            st.info("Used fallback merge branch structure.")
            return fallback
        else:
            fallback = [
                {
                    "name": "Option A",
                    "description": "This is the first possible branch of the story.",
                    "children": []
                },
                {
                    "name": "Option B",
                    "description": "This is the second possible branch of the story.",
                    "children": []
                }
            ]
            st.info("Used fallback branch options.")
            return fallback

# Helper function to assign unique IDs to all nodes
def assign_node_ids(node, prefix="node", index=0):
    node_id = f"{prefix}_{index}"
    node["id"] = node_id
    
    for i, child in enumerate(node.get("children", [])):
        child_prefix = f"{prefix}_{index}"
        assign_node_ids(child, child_prefix, i)
    
    return node

# Function to find a node by ID
def find_node_by_id(node, target_id):
    if node.get("id") == target_id:
        return node
    
    for child in node.get("children", []):
        found = find_node_by_id(child, target_id)
        if found:
            return found
    
    return None

# Helper function to update node children - defined at global scope
def update_node_children(node, path, index, new_children):
    if index >= len(path):
        # We've reached the target node, APPEND new children instead of replacing
        if "children" not in node:
            node["children"] = []
        
        # If this is a linear story node, preserve the existing child
        existing_children = node.get("children", [])
        
        # Check if we're adding a list of children or a single child
        if isinstance(new_children, list):
            node["children"] = existing_children + new_children
        else:
            node["children"] = existing_children + [new_children]
        return True
    
    if "children" not in node or index >= len(path) or path[index] >= len(node["children"]):
        return False
    
    # Continue traversing
    return update_node_children(node["children"][path[index]], path, index + 1, new_children)

class StoryNode:
    def __init__(self, id, name, description, is_merge_point=False, merge_target_id=None):
        self.id = id
        self.name = name
        self.description = description
        self.is_merge_point = is_merge_point
        self.merge_target_id = merge_target_id
        self.children = []
    
    def to_dict(self):
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "children": [child.to_dict() for child in self.children]
        }
        if self.is_merge_point:
            result["is_merge_point"] = True
            result["merge_target_id"] = self.merge_target_id
        return result

# Helper function to update the story data structure
def process_merge_branch(story_data):
    """Process the story data to handle merge branches properly"""
    # Create a mapping of node IDs to their objects
    node_map = {}
    
    # Function to recursively collect all nodes
    def collect_nodes(node, parent=None):
        node_id = node.get("id")
        if node_id:
            node_map[node_id] = {"node": node, "parent": parent}
        
        for child in node.get("children", []):
            collect_nodes(child, node)
    
    # Collect all nodes
    collect_nodes(story_data)
    
    # Now process merge points
    merge_points = []
    for node_id, data in node_map.items():
        node = data["node"]
        if node.get("is_merge_point") and node.get("merge_target_id"):
            merge_points.append(node)
    
    # Return the processed data and mappings
    return story_data, node_map, merge_points

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
        try:
            story_data = get_story_json(prompt, is_initial_story=True)
            # Assign unique IDs to all nodes
            st.session_state.story_data = assign_node_ids(story_data)
            # Process merge branches
            st.session_state.story_data, _, _ = process_merge_branch(st.session_state.story_data)
            st.success("Story generated successfully!")
        except Exception as e:
            st.error(f"Error generating story: {str(e)}")
            st.write("Trying fallback story generation...")
            try:
                # Use the fallback story structure
                st.session_state.story_data = {
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
                # Assign unique IDs to all nodes
                st.session_state.story_data = assign_node_ids(st.session_state.story_data)
                st.success("Used fallback story structure.")
            except Exception as fallback_error:
                st.error(f"Fallback also failed: {str(fallback_error)}")
                st.session_state.story_data = None

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
            .node.merge-point circle {
                fill: #a98adc;
                stroke: #7e53c5;
                stroke-width: 2px;
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
            .link.merge-link {
                stroke: #a98adc;
                stroke-dasharray: 5, 5;
            }
            .selected-node circle {
                fill: #ff7f0e;
                stroke: #d26013;
                stroke-width: 2px;
            }
            h3 {
                margin-top: 5px;
                color: #333;
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
                if (!node.id) node.id = "node_" + Math.random().toString(36).substr(2, 9);
                
                if (node.children && Array.isArray(node.children)) {
                    node.children.forEach(processNode);
                }
                return node;
            }
            
            const processedData = processNode(JSON.parse(JSON.stringify(data)));
            
            // Create a flat list of all nodes to handle merge points
            const allNodes = [];
            function collectNodes(node) {
                allNodes.push(node);
                if (node.children && Array.isArray(node.children)) {
                    node.children.forEach(collectNodes);
                }
            }
            collectNodes(processedData);
            
            // Create virtual links for merge points
            const mergeLinks = [];
            allNodes.forEach(node => {
                if (node.is_merge_point && node.merge_target_id) {
                    const targetNode = allNodes.find(n => n.id === node.merge_target_id);
                    if (targetNode) {
                        mergeLinks.push({
                            source: node,
                            target: targetNode,
                            isMergeLink: true
                        });
                    }
                }
            });
            
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
                .attr("fill", function(d) { return d === "merge-arrow" ? "#a98adc" : "#999"; })
                .attr("stroke", function(d) { return d === "merge-arrow" ? "#7e53c5" : "#666"; })
                .attr("stroke-width", 1);
                
                            // Create tree layout - vertical orientation (top to bottom)
            const root = d3.hierarchy(processedData);
            const nodeCount = root.descendants().length;
            
            // Process data for visualization
            // First, extract the merge points and store by ID for quick lookup
            const mergePoints = new Map();
            const nodeMap = new Map();
            
            // First pass - collect all node references
            root.descendants().forEach(d => {
                nodeMap.set(d.data.id, d);
                
                if (d.data.is_merge_point) {
                    mergePoints.set(d.data.id, {
                        source: d,
                        targetId: d.data.merge_target_id
                    });
                }
            });
            
            // Create a Y-axis spacing variable based on the number of nodes
            const ySpacing = Math.min(120, (height * 0.8) / (nodeCount + 1));
            
            // Create tree layout - vertical orientation (top to bottom)
            const treeLayout = d3.tree()
                .size([width * 0.7, nodeCount <= 5 ? height * 0.7 : height * 0.85]) // Adaptive sizing
                .nodeSize([0, ySpacing]) // Set consistent vertical spacing between nodes
                .separation(function(a, b) { return 3; }); // Increase horizontal separation
            
            // Apply the layout
            treeLayout(root);
            
            // Post-process node positions for branches
            root.descendants().forEach(function(d) {
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
            const link = svg.selectAll(".regular-link")
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
            
            // Add merge links
            const mergeLinks = [];
            function collectMergeLinks(node, ancestors = []) {
                if (node.data && node.data.is_merge_point && node.data.merge_target_id) {
                    const targetNode = nodeMap.get(node.data.merge_target_id);
                    if (targetNode) {
                        mergeLinks.push({
                            source: node,
                            target: targetNode,
                            isMergeLink: true
                        });
                    }
                }
                
                if (node.children) {
                    const newAncestors = [...ancestors, node];
                    node.children.forEach(child => collectMergeLinks(child, newAncestors));
                }
            }
            
            collectMergeLinks(root);
            
            // Add merge links
            const mergeLink = svg.selectAll(".merge-link")
                .data(mergeLinks)
                .enter()
                .append("path")
                .attr("class", "link merge-link")
            .style("stroke-width", 2.5)
            .style("stroke-dasharray", "5,5")
                .attr("d", function(d) {
                    // Create a curved path from source to target
                    // Calculate control points for a more natural curve
                    const dx = d.target.x - d.source.x;
                    const dy = d.target.y - d.source.y;
                    
                    // Use different curve styles based on relative positions
                    if (d.target.y < d.source.y) {
                        // Target is above source - curve upward
                        const midX = (d.source.x + d.target.x) / 2;
                        const midY = d.target.y - 30; // Control point above target
                        
                        return "M" + d.source.x + "," + d.source.y +
                               "Q" + midX + "," + midY +
                               " " + d.target.x + "," + d.target.y;
                    } else if (Math.abs(d.source.x - d.target.x) > 100) {
                        // Target is far to the side - use an S-curve
                        return "M" + d.source.x + "," + d.source.y +
                               "C" + (d.source.x) + "," + (d.source.y + 50) +
                               " " + (d.target.x) + "," + (d.target.y - 50) +
                               " " + d.target.x + "," + d.target.y;
                    } else {
                        // Default curve
                        const midX = (d.source.x + d.target.x) / 2;
                        const midY = (d.source.y + d.target.y) / 2 - 30;
                        
                        return "M" + d.source.x + "," + d.source.y +
                               "Q" + midX + "," + midY +
                               " " + d.target.x + "," + d.target.y;
                    }
                })
                .attr("marker-end", "url(#merge-arrow)");
            
            // Create node groups
            const node = svg.selectAll(".node")
                .data(root.descendants())
                .enter()
                .append("g")
                .attr("class", function(d) { 
                    let classList = "node";
                    if (d.data.is_merge_point) classList += " merge-point";
                    if (d.children) classList += " node--internal";
                    else classList += " node--leaf";
                    return classList;
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
                        .attr("fill", "white")
                        .attr("fill-opacity", 0.8)
                        .attr("rx", 3)
                        .attr("ry", 3);
                });
            
            // Function to show node details
            function showNodeDetails(nodeData) {
                const detailsDiv = document.getElementById('node-details');
                
                // Create HTML content
                let content = "<h4>" + (nodeData.name || 'Unnamed Node') + "</h4>" +
                              "<p>" + (nodeData.description || 'No description available.') + "</p>";
                
                if (nodeData.is_merge_point) {
                    // Find the target node name
                    const targetNode = allNodes.find(n => n.id === nodeData.merge_target_id);
                    const targetName = targetNode ? targetNode.name : nodeData.merge_target_id;
                    
                    content += "<p><strong>Merge Point:</strong> This branch reconnects to the main story.</p>";
                    content += "<p><strong>Merges with:</strong> " + targetName + "</p>";
                }
                
                if (nodeData.children && nodeData.children.length > 0) {
                    content += "<p><strong>Options:</strong></p><ul>";
                    nodeData.children.forEach(function(child) {
                        content += "<li>" + child.name + "</li>";
                    });
                    content += "</ul>";
                } else if (!nodeData.is_merge_point) {
                    content += "<p><em>This is an endpoint of the story.</em></p>";
                }
                
                content += "<p><strong>Node ID:</strong> " + nodeData.id + "</p>";
                
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
        name = prefix + node.get("name", "Unnamed") + f" (ID: {node.get('id', 'unknown')})"
        
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
    
    selected_node = st.selectbox("Select a node to extend:", node_options)
    
    # Only show extension options if a real node is selected
    if selected_node != "Select a node to extend...":
        # Get context for the selected node to help the AI generate relevant branches
        selected_node_context = ""
        selected_node_id = ""
        if selected_node in st.session_state.node_paths:
            path = st.session_state.node_paths[selected_node]
            node = get_node_by_path(st.session_state.story_data, path)
            if node:
                selected_node_context = f"Selected node: {node.get('name')}\nDescription: {node.get('description')}"
                selected_node_id = node.get('id', '')
        
        # Choose between regular branch or merge branch
        branch_type = st.radio(
            "Branch Type",
            ["Regular Branch", "Merge Branch (connects back to main story)"],
            index=0
        )
        
        if branch_type == "Regular Branch":
            extension_prompt = st.text_area(
                "How would you like to extend this branch?", 
                f"Create two additional branches from '{selected_node.split('→ ')[-1].split(' (ID:')[0]}'"
            )
            
            if st.button("Extend Branch"):
                with st.spinner('Generating branch options...'):
                    # Create the full context for the API call
                    full_prompt = f"""
                    {selected_node_context}
                    
                    {extension_prompt}
                    """
                    
                    # Get branch options from the API
                    branch_options = get_story_json(full_prompt, is_initial_story=False)
                    
                    # Find the node to extend
                    if selected_node in st.session_state.node_paths:
                        path = st.session_state.node_paths[selected_node]
                        
                        # Use the global update_node_children function
                        
                        # Update the story tree
                        success = update_node_children(st.session_state.story_data, path, 0, branch_options)
                        
                        if success:
                            # Get the node that was updated
                            updated_node = get_node_by_path(st.session_state.story_data, path)
                            branch_count = len(updated_node.get("children", []))
                            original_count = branch_count - len(branch_options)
                            
                            # Assign IDs to the new nodes
                            for i, child in enumerate(updated_node.get("children", [])[original_count:]):
                                child_id = f"{selected_node_id}_branch_{i+original_count}"
                                child["id"] = child_id
                                # Recursively assign IDs to any children
                                if "children" in child and child["children"]:
                                    assign_node_ids(child, child_id, 0)
                            
                            if original_count > 0:
                                message = f"Successfully added {len(branch_options)} new branches to the story while preserving the original {original_count} path(s)!"
                            else:
                                message = f"Successfully added {len(branch_options)} new branches to the story!"
                            
                            st.success(message)
                            # Force a rerun to update the visualization
                            st.rerun()
                        else:
                            st.error("Failed to update the story structure. Please try again.")
        else:
            # For merge branches, we need a target node to merge with
            st.subheader("Select Merge Target")
            
            # Get all possible merge targets (all nodes except the current one and its descendants)
            all_nodes = []
            
            def collect_all_nodes(node, path=None, prefix="", exclude_paths=None):
                if path is None:
                    path = []
                if exclude_paths is None:
                    exclude_paths = []
                
                # Skip this node and its descendants if it's in the excluded paths
                for ex_path in exclude_paths:
                    if len(path) >= len(ex_path) and path[:len(ex_path)] == ex_path:
                        return []
                
                current_path = path.copy()
                name = prefix + node.get("name", "Unnamed") + f" (ID: {node.get('id', 'unknown')})"
                
                result = [(name, node.get('id', ''))]
                
                for i, child in enumerate(node.get("children", [])):
                    child_path = current_path.copy()
                    child_path.append(i)
                    child_results = collect_all_nodes(child, child_path, prefix + "→ ", exclude_paths)
                    result.extend(child_results)
                    
                return result
            
            # Get the path of the selected node to exclude it and its descendants
            exclude_path = st.session_state.node_paths.get(selected_node, [])
            
            # Collect all nodes except the selected one and its descendants
            all_nodes = collect_all_nodes(st.session_state.story_data, [], "", [exclude_path])
            
            # Create a dropdown of potential merge targets
            merge_targets = [f"{name} ({node_id})" for name, node_id in all_nodes]
            merge_target = st.selectbox("Select which node this branch should merge back into:", merge_targets)
            
            # Extract the node ID from the selected merge target
            merge_target_id = ""
            if merge_target:
                merge_target_id = merge_target.split("(ID: ")[1].rstrip(")")
            
            merge_prompt = st.text_area(
                "Describe how this branch should merge back to the main story:",
                f"Create a branch that starts from '{selected_node.split('→ ')[-1].split(' (ID:')[0]}' and eventually reconnects to '{merge_target.split(' (ID:')[0]}'"
            )
            
            if st.button("Create Merge Branch"):
                with st.spinner('Generating merge branch...'):
                    # Create the full context for the API call
                    full_prompt = f"""
                    Current branch node: {selected_node_context}
                    
                    Target node to merge with: {merge_target}
                    
                    Please create a narrative branch that starts from the current node and eventually 
                    reconnects with the target node. Explain how the character or plot returns to the main storyline.
                    
                    {merge_prompt}
                    """
                    
                    # Get merge branch from the API
                    merge_branch = get_story_json(full_prompt, is_initial_story=False, is_merge_branch=True, merge_target_id=merge_target_id)
                    
                    # Set the merge target ID
                    merge_branch["merge_target_id"] = merge_target_id
                    merge_branch["is_merge_point"] = True
                    merge_branch["id"] = f"{selected_node_id}_merge_{merge_target_id}"
                    
                    # Find the node to extend
                    if selected_node in st.session_state.node_paths:
                        path = st.session_state.node_paths[selected_node]
                        
                        # Update the story tree with the merge branch
                        success = update_node_children(st.session_state.story_data, path, 0, merge_branch)
                        
                        if success:
                            # Process merge branches
                            st.session_state.story_data, _, _ = process_merge_branch(st.session_state.story_data)
                            
                            st.success(f"Successfully added a merge branch that connects back to the main story at '{merge_target.split(' (ID:')[0]}'!")
                            # Force a rerun to update the visualization
                            st.rerun()
                        else:
                            st.error("Failed to update the story structure. Please try again.")
                        
                        # Use the global update_node_children function