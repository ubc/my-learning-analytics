import React, { useState } from 'react'
import { styled } from '@mui/material/styles'
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
	const [messages, setMessages] = useState([])
	const [typingState, setTypingState] = useState(false)

	const handleSubmit = async (e) => {
		e.preventDefault()

		const input = e.target[0].value
		if (input.trim()) {
			// User message
			setMessages((prev) => [{ text: input, role: 'user' }, ...prev])

			console.log('User message: ' + input)
			e.target[0].value = ''
			// LLM message
			setTypingState(true)
			try {
				const response = await useOllama(input)
				setMessages((prev) => [{ text: response, role: 'assistant' }, ...prev])
			} catch (error) {
				console.error(error)
			}
			// await processMessage(messages)
			setTypingState(false)
		}
	}

	return (
		<Root>
			<h2 style={{ margin: 0, paddingLeft: '20px', paddingTop: '10px' }}>
				AI Assistant
			</h2>
			{/* Background */}
			<div style={styles.outerContainer}>
				<div style={styles.innerContainer}>
					<div style={styles.chatHistory}>
						{messages.map((message, index) => (
							<p
								key={index}
								style={
									message.role === 'user'
										? styles.userMessage
										: styles.responseMessage
								}>
								{message.text}
							</p>
						))}
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
								Type
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
		padding: '20px 0', // Combined top and horizontal padding
		height: '88vh',
		width: '40vw',
		minWidth: '40vw',
		maxWidth: '40vw',
		overflow: 'hidden',
	},
	innerContainer: {
		display: 'flex',
		margin: '0 auto',
		backgroundColor: '#f5f5f5',
		border: '2px solid black',
		height: '100%',
		flexDirection: 'column',
		overflow: 'hidden',
	},
	chatHistory: {
		display: 'flex',
		flexDirection: 'column-reverse',
		flex: 2, // Simplified flex shorthand
		padding: '10px',
		overflowY: 'auto',
	},
	userMessage: {
		alignSelf: 'flex-end',
		marginBottom: '8px',
		padding: '8px',
		backgroundColor: '#ffadad',
		borderRadius: '10px', // Increased radius for a smoother look
		maxWidth: '80%',
	},
	responseMessage: {
		alignSelf: 'flex-start',
		marginBottom: '8px',
		padding: '8px',
		backgroundColor: '#cce5ff',
		borderRadius: '10px', // Consistent with userMessage
		maxWidth: '80%',
	},
	formContainer: {
		height: '100px',
		padding: '12px',
		display: 'flex',
		justifyContent: 'center',
		alignItems: 'center',
		borderTop: '2px solid black',
		backgroundColor: '#ffffff', // Ensures contrast with the chat area
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
		backgroundColor: 'navy',
		color: 'white',
		border: 'none',
		borderRadius: '8px',
		cursor: 'pointer',
	},
}

export default LearningCoach
