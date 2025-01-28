const useOllama = async (message) => {
	console.log('User message 2: ' + message)
	try {
		// Change path URL (look into urls.py nad views.py)
		const response = await fetch('/api/learningCoach', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ message: message }),
		})

		console.log('test')

		if (response.ok) {
			const data = await response.json()

			// Ensure the response contains the expected structure
			if (data.message && data.message.content) {
				console.log(data.message.content)
				return data.message.content
			} else {
				console.error('Unexpected response format:', data)
				return null
			}
		} else {
			const errorData = await response.json()
			console.error(
				'Failed to communicate with the server:',
				errorData.error || 'Unknown error'
			)
			return null
		}
	} catch (error) {
		console.error('An error occurred: ', error.message)
		return null
	}
}

export default useOllama
