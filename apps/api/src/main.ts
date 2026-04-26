import "reflect-metadata";

import { ValidationPipe } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import type { NextFunction, Request, Response } from "express";
import helmet from "helmet";

import { AppModule } from "./app.module.js";

function createRateLimiter(options: {
  windowMs: number;
  maxRequests: number;
}): (request: Request, response: Response, next: NextFunction) => void {
  const buckets = new Map<string, { count: number; resetAt: number }>();

  return (request: Request, response: Response, next: NextFunction): void => {
    const now = Date.now();

    if (buckets.size > 10_000) {
      for (const [bucketKey, bucket] of buckets.entries()) {
        if (bucket.resetAt <= now) {
          buckets.delete(bucketKey);
        }
      }
    }

    const clientIp =
      request.ip ||
      (Array.isArray(request.ips) && request.ips.length > 0
        ? request.ips[0]
        : "unknown");
    const key = `${clientIp}:${request.path}`;
    const existing = buckets.get(key);

    if (!existing || existing.resetAt <= now) {
      buckets.set(key, { count: 1, resetAt: now + options.windowMs });
      next();
      return;
    }

    if (existing.count >= options.maxRequests) {
      const retryAfterSeconds = Math.max(
        1,
        Math.ceil((existing.resetAt - now) / 1000),
      );
      response.setHeader("Retry-After", String(retryAfterSeconds));
      response.status(429).json({
        statusCode: 429,
        message: "Too many requests. Please try again shortly.",
        error: "Too Many Requests",
      });
      return;
    }

    existing.count += 1;
    buckets.set(key, existing);
    next();
  };
}

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);

  const authRateLimiter = createRateLimiter({
    windowMs: 60_000,
    maxRequests: 15,
  });
  const plaidRateLimiter = createRateLimiter({
    windowMs: 60_000,
    maxRequests: 30,
  });

  app.use((request: Request, response: Response, next: NextFunction) => {
    if (
      request.path.startsWith("/api/auth") ||
      request.path.startsWith("/auth")
    ) {
      authRateLimiter(request, response, next);
      return;
    }

    if (
      request.path.startsWith("/api/plaid") ||
      request.path.startsWith("/plaid")
    ) {
      plaidRateLimiter(request, response, next);
      return;
    }

    next();
  });

  app.use(
    helmet({
      crossOriginEmbedderPolicy: false,
    }),
  );

  const corsOrigins = (process.env.CORS_ORIGINS ?? "")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);

  app.enableCors({
    origin: corsOrigins.length > 0 ? corsOrigins : false,
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
    maxAge: 86400,
  });

  app.setGlobalPrefix("api");
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidUnknownValues: true,
    }),
  );

  const port = Number(process.env.API_PORT ?? 4000);
  await app.listen(port);
}

bootstrap();
