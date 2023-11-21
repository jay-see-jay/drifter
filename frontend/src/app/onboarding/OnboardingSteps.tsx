'use client'
import OnboardingStep from '@/app/onboarding/OnboardingStep'
import { useEffect, useState, useReducer } from 'react'
import { User } from '@/lib/database'
import isGmailSyncComplete from '@/actions/isGmailSyncComplete'
import isGmailWatchSetUp from '@/actions/isGmailWatchSetUp'

export type StepStatus = 'pending' | 'in_progress' | 'complete'

export type Step = {
	description: string
	status: StepStatus
	hasData: boolean | undefined
	action?: (userId: number) => Promise<boolean>
}

const steps: Step[] = [
	{
		description: 'Creating your account',
		status: 'pending',
		hasData: undefined,
	},
	{
		description: 'Syncing with Gmail',
		status: 'pending',
		hasData: undefined,
		action: isGmailSyncComplete,
	},
	{
		description: 'Subscribing to new emails',
		status: 'pending',
		hasData: undefined,
		action: isGmailWatchSetUp,
	},
]

function randomInterval(): number {
	return Math.random() * 2000 + 250
}

export type StepsDispatchAction = {
	type: 'next'
	payload: {
		step: number | undefined
	}
} | {
	type: 'update'
	payload: {
		step: number
		hasData: boolean
	}
}

function getInProgressStep(state: Step[]): number | undefined {
	for (let i = 0; i < state.length; i++) {
		const step = state[i]
		if (step && step.status === 'in_progress') {
			return i
		}
	}
	return undefined
}

function getNextStep(inProgressStep: number | undefined): number {
	if (inProgressStep === undefined) return 0
	return inProgressStep + 1
}

function stepsReducer(state: Step[], action: StepsDispatchAction): Step[] {
	if (action.type === 'next') {
		const inProgressStep = action.payload.step
		const nextStep = getNextStep(inProgressStep)
		
		const nextState = [...state]

		if (inProgressStep != undefined) {
			nextState[inProgressStep].status = 'complete'
		}
		if (nextStep < state.length) {
			nextState[nextStep].status = 'in_progress'
		}
		return nextState
	}

	if (action.type === 'update') {
		const { step, hasData } = action.payload
		const nextState = [...state]

		nextState[step].hasData = hasData

		return nextState
	}

	throw Error('Could not find action type')
}

type OnboardingStepsProps = {
	user: User
}

export default function OnboardingSteps({ user }: OnboardingStepsProps) {
	const [ms, setMs] = useState<number>(0)
	const [intervalState, setIntervalState] = useState<NodeJS.Timeout | undefined>(undefined)
	const [stepsStatus, setStepsStatus] = useReducer(stepsReducer, steps)
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
		const isLastStepComplete = stepsStatus[stepsStatus.length - 1 ].status === 'complete'
		if (isLastStepComplete) {
			clearInterval(intervalState)
			setIntervalState(undefined)
			return
		}
		const shouldProgress = ms >= lastChangeAtSeconds + waitFor
		if (! shouldProgress) return
		
		const inProgressStep = getInProgressStep(stepsStatus)

		setStepsStatus({
			type: 'next',
			payload: { step: inProgressStep }
		})
		setLastChangeAtSeconds(ms)
		setWaitFor(randomInterval())
		
	}, [ms, intervalState, lastChangeAtSeconds, stepsStatus, waitFor])
	
	return (
		<ul>
			{stepsStatus.map((step, index) => {
				return (
					<OnboardingStep
						key={index}
						step={step}
						stepIndex={index}
						userId={user.pk}
						status={stepsStatus[index].status}
						updateStepStatus={setStepsStatus}
					/>
				)
			})}
		</ul>
	)
}