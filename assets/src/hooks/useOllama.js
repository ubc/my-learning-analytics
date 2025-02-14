const useOllama = async (message, onStreamChunk) => {
	console.log('UM: ' + message)
	try {
		// Change path URL (look into urls.py nad views.py)
		const response = await fetch('/api/learningCoach', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ message: message }),
		})

		if (!response.ok) {
			const errorData = await response.json()
			console.error('Failed to communicate with the server:', errorData)
			return null
		}

		const reader = response.body.getReader()
		const decoder = new TextDecoder('utf-8')
		let buffer = ''

		let results = ''

		while (true) {
			const { done, value } = await reader.read()

			// Finished sending messages, break out of loop
			if (done) {
				break
			}

			const chunk = decoder.decode(value, { stream: true })
			buffer += chunk

			let boundaryIndex

			while ((boundaryIndex = buffer.indexOf('\n')) !== -1) {
				const jsonChunk = buffer.slice(0, boundaryIndex).trim() // Extract JSON
				buffer = buffer.slice(boundaryIndex + 1) // Remove processed part

				if (!jsonChunk) continue // Ignore empty chunks

				try {
					const parsed = JSON.parse(jsonChunk)
					const text = parsed.message?.content || ''
					results += text // Append to full message

					if (onStreamChunk) onStreamChunk(text)
				} catch (error) {
					console.warn('Skipping invalid JSON chunk:', jsonChunk)
				}
			}
		}
    console.log('CM: ' + results)
		return results
	} catch (error) {
		console.error('An error occurred: ', error.message)
		return null
	}
}

export default useOllama
