import React, { useState } from 'react'
import { styled } from '@mui/material/styles'
import Markdown from 'react-markdown'
import useOllama from '../hooks/useOllama'

const PREFIX = 'LearningCoach'

const classes = {
	root: `${PREFIX}-root`,
	paper: `${PREFIX}-paper`,
	content: `${PREFIX}-content`,
	container: `${PREFIX}-container`,
	grow: `${PREFIX}-grow`,
}

// Styled component
const Root = styled('div')(({ theme }) => ({
	[`& .${classes.root}`]: {
		display: 'flex',
		height: '100vh',
	},
	[`& .${classes.grow}`]: {
		flexGrow: 1,
	},
}))

const LearningCoach = () => {
	const [messages, setMessages] = useState([
		{
			text: 'What are you working on today, and how can I help you stay on track?',
			role: 'assistant',
		},
	])
	const [typingState, setTypingState] = useState(false)

	const handleSubmit = async (e) => {
		e.preventDefault()

		const input = e.target[0].value
		if (!input) return

		// User message
		setMessages((prev) => [{ text: input, role: 'user' }, ...prev])
		e.target[0].value = ''

		// Assistant Message
		setMessages((prev) => [{ text: '', role: 'assistant' }, ...prev])

		setTypingState(true)

		try {
			await useOllama(input, (chunk) => {
				// Appends chunk to last message
				setMessages((prev) => {
					const updatedMessages = [...prev]
					updatedMessages[0] = {
						...updatedMessages[0],
						text: updatedMessages[0].text + chunk,
					}

					return updatedMessages
				})
			})
		} catch (error) {
			console.error(error)
		}

		setTypingState(false)
	}

	return (
		<Root>
			<h2
				style={{
					paddingLeft: '20px',
					borderBottom: '2px solid black',
					margin: '0',
					marginTop: '5px',
				}}>
				AI Assistant
			</h2>
			{/* Background */}
			<div style={styles.outerContainer}>
				<div style={styles.innerContainer}>
					<div style={styles.chatHistory}>
						{messages.map((message, index) => {
							if (message.role === 'user') {
								return (
									<p key={index} style={styles.userMessage}>
										{message.text}
									</p>
								)
							} else {
								return (
									<div key={index} style={styles.responseMessage}>
										<Markdown>{message.text}</Markdown>
									</div>
								)
							}
						})}
					</div>
					<div style={styles.formContainer}>
						<form
							style={{
								display: 'flex',
								flexDirection: 'row',
								width: '100%',
								padding: '12px',
							}}
							onSubmit={handleSubmit}>
							<input
								type='text'
								placeholder='Type Away...'
								style={styles.input}
							/>
							<button
								type='submit'
								style={styles.button}
								disabled={typingState}>
								Send
							</button>
						</form>
					</div>
				</div>
			</div>
		</Root>
	)
}

const styles = {
	outerContainer: {
		height: '93vh',
		width: '100%',
		overflow: 'hidden',
		marginTop: '10px',
		paddingBottom: '10px',
	},
	innerContainer: {
		display: 'flex',
		backgroundColor: '#F8F9FA',
		border: '1px solid black',
		height: '100%',
		marginLeft: '10px',
		marginRight: '10px',
		flexDirection: 'column',
		overflow: 'auto',
		borderRadius: '10px',
	},
	chatHistory: {
		display: 'flex',
		flexDirection: 'column-reverse',
		flex: 1,
		padding: '10px',
		overflowY: 'auto',
	},
	userMessage: {
		alignSelf: 'flex-end',
		marginBottom: '8px',
		padding: '8px',
		backgroundColor: '#E9ECEF',
		borderRadius: '8px',
		maxWidth: '80%',
	},
	responseMessage: {
		paddingLeft: '8px',
		paddingRight: '8px',
		backgroundColor: '#FFFFFF',
		borderRadius: '8px', // Consistent with userMessage
		maxWidth: '80%',
		border: '1px solid #DEE2E6',
		borderRadius: '8px',
	},
	formContainer: {
		minHeight: '60px',
		padding: '12px',
		display: 'flex',
		justifyContent: 'center',
		alignItems: 'center',
		borderTop: '2px solid black',
		backgroundColor: '#F8F9FA', // Ensures contrast with the chat area
	},
	input: {
		flex: 1,
		padding: '10px', // Increased padding for a better input feel
		border: '1px solid navy', // Reduced thickness for a cleaner look
		borderRadius: '5px', // Slight rounding for a modern look
		marginRight: '10px', // Increased margin for better spacing
	},
	button: {
		padding: '10px 20px', // Added horizontal padding for better button dimensions
		backgroundColor: '#ab7200',
		color: 'white',
		border: 'none',
		borderRadius: '8px',
		cursor: 'pointer',
	},
}

export default LearningCoach
