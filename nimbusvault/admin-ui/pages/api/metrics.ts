import { NextApiRequest, NextApiResponse } from 'next';
import client from 'prom-client';

const register = new client.Registry();
client.collectDefaultMetrics({ register });

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  res.setHeader('Content-Type', register.contentType);
  res.send(await register.metrics());
}
