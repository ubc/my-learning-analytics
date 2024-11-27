import React, { useState } from 'react'
import { styled } from '@mui/material/styles'

import { IconButton, Tooltip, Drawer } from '@mui/material'
import { Close, Assistant } from '@mui/icons-material'

import LearningCoach from '../containers/LearningCoach'

const ChatButton = styled(IconButton)(({ theme }) => ({
	position: 'fixed',
	bottom: theme.spacing(2),
	right: theme.spacing(2),
	zIndex: 1000,
	backgroundColor: theme.palette.primary.main,
	color: theme.palette.common.white,
	'&:hover': {
		backgroundColor: theme.palette.primary.dark,
	},
	borderRadius: '50%',
}))

const Sidebar = () => {
	const [isOpen, setIsOpen] = useState(false)

	const toggleChat = () => {
		setIsOpen(!isOpen)
	}

	return (
		<div className='sidebar'>
			<Tooltip title={isOpen ? 'Close Chat' : 'Open Chat'}>
				<ChatButton onClick={toggleChat}>
					{isOpen ? <Close /> : <Assistant />}
				</ChatButton>
			</Tooltip>
			<Drawer open={isOpen} anchor='right' onClose={toggleChat}>
				<LearningCoach />
			</Drawer>
		</div>
	)
}

export default Sidebar
