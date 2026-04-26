import { z } from "zod";

const envSchema = z.object({
  API_PORT: z.coerce.number().int().positive().default(4000),
  DATABASE_URL: z
    .string()
    .min(1)
    .startsWith("postgresql://", "DATABASE_URL must start with postgresql://"),
  DIRECT_URL: z
    .string()
    .optional()
    .refine(
      (value) => value === undefined || value.startsWith("postgresql://"),
      {
        message: "DIRECT_URL must start with postgresql://",
      },
    ),
  JWT_SECRET: z.string().min(32, "JWT_SECRET must be at least 32 characters"),
  MFA_REQUIRED: z
    .preprocess((value) => {
      if (value === undefined || value === null || value === "") {
        return undefined;
      }

      if (typeof value === "boolean") {
        return value;
      }

      if (typeof value === "string") {
        return value.toLowerCase() === "true";
      }

      return undefined;
    }, z.boolean().optional())
    .default(false),
  WEBAUTHN_RP_ID: z.string().optional(),
  WEBAUTHN_RP_NAME: z.string().optional(),
  WEBAUTHN_ORIGINS: z.string().optional(),
  PLAID_CLIENT_ID: z.string().optional(),
  PLAID_SECRET: z.string().optional(),
  PLAID_SANDBOX_SECRET: z.string().optional(),
  PLAID_DEVELOPMENT_SECRET: z.string().optional(),
  PLAID_PRODUCTION_SECRET: z.string().optional(),
  PLAID_ENV: z
    .enum(["sandbox", "development", "production"])
    .default("sandbox"),
  PLAID_PRODUCTS: z.string().default("transactions"),
  PLAID_COUNTRY_CODES: z.string().default("US"),
  PLAID_PFC_TAXONOMY_VERSION: z.string().optional(),
  PLAID_REDIRECT_URI: z.preprocess((value) => {
    if (value === undefined || value === null || value === "") {
      return undefined;
    }

    return value;
  }, z.string().url().optional()),
  PLAID_ACCESS_TOKEN_ENCRYPTION_KEY: z
    .string()
    .min(1)
    .refine(
      (value) => {
        try {
          return Buffer.from(value, "base64").length === 32;
        } catch {
          return false;
        }
      },
      {
        message:
          "PLAID_ACCESS_TOKEN_ENCRYPTION_KEY must be a base64-encoded 32-byte key",
      },
    ),
  PLAID_TOKEN_MAINTENANCE_KEY: z.string().optional(),
  CORS_ORIGINS: z.string().optional(),
});

export function validateEnv(
  config: Record<string, unknown>,
): Record<string, unknown> {
  const parsed = envSchema.safeParse(config);

  if (!parsed.success) {
    const details = parsed.error.issues
      .map((issue) => `${issue.path.join(".") || "env"}: ${issue.message}`)
      .join("; ");

    throw new Error(`Invalid environment configuration: ${details}`);
  }

  return parsed.data;
}
