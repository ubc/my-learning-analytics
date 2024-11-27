
import requests
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def llama3(request):
    data = json.loads(request.body)
    message = data.get('message', '')
    print('=============')
    print('message: ' + message)

    url = "http://host.docker.internal:11434/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3",
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False,
    }

    try:
        response = requests.post(url, headers=headers, json=data, stream=False)
        response.raise_for_status()

        response_data = response.json()

        print('=============')
        print(response_data["message"]["content"])
        print('=============')

        return JsonResponse(response_data, status=response.status_code)

    except requests.exceptions.RequestException as e:
        print('Request failed:', str(e))
        return JsonResponse({'error': str(e)}, status=500)
    except ValueError:
        print('Invalid JSON response recieved')
        return JsonResponse({'error': 'Invalid JSON response recieved from the external service.'}, status=500)

# TODO: Add chat history to this AI
# TODO: Actually read the research paper and see what the prompting is about
# TODO: Figure out how to import data into myLA