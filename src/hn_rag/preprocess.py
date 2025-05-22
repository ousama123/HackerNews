import json

with open("data/topstories.json", "r") as f:
    data = json.load(f)

# Create mappings for easy lookup
comments_dict = {comment["id"]: comment for comment in data.get("comments", [])}
users_dict = {user["id"]: user for user in data.get("users", [])}


# TODO is it the best way?
def replace_references_with_objects(item):
    """Recursively replace user IDs and comment IDs with actual objects"""
    # Replace 'by' field with user object
    if "by" in item and item["by"] in users_dict:
        item["by"] = users_dict[item["by"]].copy()

    # Replace 'kids' IDs with actual comment objects
    if "kids" in item and item["kids"]:
        kids_comments = []
        for kid_id in item["kids"]:
            if kid_id in comments_dict:
                # Get the comment and make a copy
                comment = comments_dict[kid_id].copy()
                # Recursively process this comment too
                comment = replace_references_with_objects(comment)
                kids_comments.append(comment)
        item["kids"] = kids_comments

    return item


# to process all stories
documents = []

for story in data.get("stories", []):
    # Create a copy and expand all references
    expanded_story = story.copy()
    expanded_story = replace_references_with_objects(expanded_story)

    # Wrap in a story object to preserve context
    story_wrapper = {"type": "story", "story": expanded_story}

    # Convert to text
    doc_text = json.dumps(story_wrapper, indent=2, ensure_ascii=False)
    documents.append(doc_text)

# Save as text file in the same data folder
with open("data/topstories.txt", "w", encoding="utf-8") as f:
    for doc in documents:
        f.write(doc)
        f.write("\n\n" + "=" * 80 + "\n\n")

print(f"Converted {len(documents)} stories to data/topstories.txt")
print(f"Processed {len(users_dict)} users and {len(comments_dict)} comments")
