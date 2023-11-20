'use client'
import OnboardingStep from '@/app/onboarding/OnboardingStep'
import { useEffect, useState, useReducer } from 'react'

const steps = [
	'Creating your account',
	'Syncing with Gmail',
	'Subscribing to new emails'
]

export type StepStatus = 'pending' | 'in_progress' | 'complete'

export type StepsState = { [key: number]: StepStatus };

function initialiseState(): StepsState {
	const state: StepsState = {}
	for (let i = 0; i < steps.length; i++) {
		state[i] = 'pending'
	}
	return state
}

type OnboardingStepsProps = {
	userEmail?: string
}

function randomInterval(): number {
	return Math.random() * 2000 + 250
}

type StepsDispatchAction = {
	type: 'next'
}

function getInProgressStep(state: StepsState): number | undefined {
	for (let i = 0; i < steps.length; i++) {
		const value = state[i]
		if (value && value === 'in_progress') {
			return i
		}
	}
	return undefined
}

function stepsReducer(state: StepsState, action: StepsDispatchAction): StepsState {
	if (action.type === 'next') {
		const inProgressStep = getInProgressStep(state)
		const nextStep = inProgressStep === undefined ? 0 : inProgressStep + 1
		
		const nextState = Object.assign({}, state)
		if (inProgressStep != undefined) {
			nextState[inProgressStep] = 'complete'
		}
		nextState[nextStep] = 'in_progress'
		return nextState
	}
	throw Error(`Could not find action type: ${action.type}`)
}

export default function OnboardingSteps({
	userEmail,
}: OnboardingStepsProps) {
	const [ms, setMs] = useState<number>(0)
	const [intervalState, setIntervalState] = useState<NodeJS.Timeout | undefined>(undefined)
	const [stepsStatus, setStepsStatus] = useReducer(stepsReducer, initialiseState())
	const [waitFor, setWaitFor] = useState(250)
	const [lastChangeAtSeconds, setLastChangeAtSeconds] = useState<number>(0)
	
	useEffect(() => {
		const interval = 100
		const intervalId = setInterval(() => {
			setMs(ms => ms + interval)
		}, interval)
		setIntervalState(intervalId)
		return () => clearInterval(intervalId)
	}, [])
	
	useEffect(() => {
		if (! intervalState) return
		const isLastStepComplete = stepsStatus[steps.length - 1 ] === 'complete'
		if (isLastStepComplete) {
			clearInterval(intervalState)
			setIntervalState(undefined)
			return
		}
		const shouldProgress = ms >= lastChangeAtSeconds + waitFor
		if (! shouldProgress) {
			console.log('Should not progree')
			return
		}
		
		console.log('Progressing...')
		setStepsStatus({ type: 'next' })
		setLastChangeAtSeconds(ms)
		setWaitFor(randomInterval())
		
	}, [ms, intervalState, lastChangeAtSeconds, stepsStatus, waitFor])
	
	return (
		<ul>
			{steps.map((step, index) => {
				return <OnboardingStep key={index} step={step} status={stepsStatus[index]} />
			})}
		</ul>
	)
}