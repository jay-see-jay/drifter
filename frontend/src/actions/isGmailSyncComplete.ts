'use server'

import Database from '@/lib/database'

const db = new Database()

export default async function isGmailSyncComplete(userId: number): Promise<boolean> {
	const messageHeader = await db.getMessageHeader(userId)
	return Boolean(messageHeader)
}