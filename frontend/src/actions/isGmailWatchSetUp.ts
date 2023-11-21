'use server'

import Database from '@/lib/database'

const db = new Database()

export default async function isGmailWatchSetUp(userId: number): Promise<boolean> {
	const historyRecord = await db.getHistoryId(userId)
	return Boolean(historyRecord)
}