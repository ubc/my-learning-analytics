// 1. Change to a sidebar design on the left
// 2. Make it add an array of messages instead of a single one

const useOllama = async (message) => {
	try {
		// Change path URL (look into urls.py nad views.py)
		const response = await fetch('/api/learningCoach', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ message: message }),
		})

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
