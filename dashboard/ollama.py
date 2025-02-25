import requests
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .persona_data import classification_prompt


@csrf_exempt
@require_POST
def llama3(request):
    data = json.loads(request.body)
    message = data.get("message", "")

    # Retrieve chat history from Django session
    session = request.session
    chat_history = session.get("chat_history", [])

    # First run initializing
    if not chat_history:
        print("Init")
        message = classification_prompt

    # Quick code to reset chat_history
    if message == "/reset":
        print("Resetting...")
        session["chat_history"] = []  # Properly clear the chat history
        session.modified = True  # Ensure session updates are saved
        return JsonResponse({"message": "Chat history reset!"}, status=200)

    chat_history.append({"role": "user", "content": message})

    url = "http://host.docker.internal:11434/api/chat"
    headers = {"Content-Type": "application/json"}

    data = {
        "model": "llama3",
        "messages": chat_history,
        "stream": True,
    }

    ai_response_content = []  # Store AI response chunks

    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        # **Pre-collect AI response before streaming**
        collected_chunks = []

        for chunk in response.iter_lines():
            if chunk:
                try:
                    json_chunk = json.loads(chunk.decode("utf-8"))
                    chunk_content = json_chunk.get("message", {}).get("content", "")

                    if chunk_content:
                        ai_response_content.append(chunk_content)

                    collected_chunks.append(json.dumps(json_chunk) + "\n")
                except json.JSONDecodeError:
                    print("Invalid JSON chunk detected")
                    collected_chunks.append(
                        json.dumps({"error": "Invalid JSON chunk"}) + "\n"
                    )

        # **Process full AI response**
        full_ai_response = "".join(ai_response_content).strip()
        print(f"Full AI Response: {full_ai_response}")  # Debugging

        chat_history.append(
            {"role": "assistant", "content": full_ai_response}
        )  # Store response

        # Save updated chat history
        session["chat_history"] = chat_history
        session.modified = True

        # **Now, stream the collected chunks**
        def stream_response():
            for chunk in collected_chunks:
                yield chunk

        print("\033c", end="")  # Clears the screen
        print("\n========= Chat History =========")
        print(json.dumps(chat_history, indent=2))
        print("================================")

        return StreamingHttpResponse(stream_response(), content_type="text/plain")

    except requests.exceptions.RequestException as e:
        return StreamingHttpResponse(
            f"Request failed: {str(e)}", content_type="text/plain"
        )


# TODO =========
# * 1. Fix the chat_history. Response bot is not working, so get that working

# 2. Add basic prompting about what the AI should expect to do (just one paragraph)
# 3. Try to pass general information to the bot (name for now)?
# 4. Try to find list of coursees they are taking
# 5. Try to find what resources they are able to access.


# ==================================   AGENDA FOR TOMORROW   ================================== #

# Tmmr Morning (prepare for the conversation):
# 1. What have I done?
# - Redesigned the frontend side panel.
# - The chatbot actually works now, albeit it's a bit slow. There were some problems with markdown on the previous model, but that's been fixed with react-markdown.
# - Fixed the pipeline between the backend and frontend (able to transit messages properly without crashing)
# - Added a django session in the backend to store previous chat_messages

# - [ ] Want to finish firt paragraph of prompting = ....
# - [ ] The llama3 chatbot has access to some of the student's information:
#     - Name
#     - List of courses taking
#     - Resources access.
#     - [ ] More about the course information, but not sure how to do that right now.

# 2. What I think we need / what I plan to do?
# - Improve on the prompting for the 3 personas.
# - Need to tell AI to categorize users still.
# - Still need to access some of the information (resources access etc)
# Does changing urls are restarting the page reset the django session? Need to figure this out, and make it unique to user.ID. How to access the user.ID?
# - Anything else???

# 3. Questions / concerns?
# - I have the 3 persona's, which I copied and pasted from the google sheet, but not sure if there's a better way to prompt this.
# - I'm still a bit confused about what the AI should have access to, and how that would help. Does this information help with categorizing the students into priority (low, med, high), or will they use this to offer advice?
# - I'm reading through the google docs and it's a bit confusing to me. It might take a while for me to understand this.
#     - Student scoring?
#     - How does the ai react to different levels of student scoring?
