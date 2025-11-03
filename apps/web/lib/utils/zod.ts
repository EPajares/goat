/* eslint-disable @typescript-eslint/no-explicit-any */

import { ZodDefault, ZodNullable, ZodObject, ZodOptional, z } from "zod";

export function getDefaults<Schema extends z.AnyZodObject>(schema: Schema) {
    return Object.fromEntries(
        Object.entries(schema.shape).map(([key, value]) => {
            if (value instanceof z.ZodDefault) return [key, value._def.defaultValue()];
            return [key, undefined];
        })
    );
}

export function hasNestedSchemaPath(
    schema: z.ZodSchema<any>, // Can be any Zod schema initially
    path: string
): boolean {
    const parts = path.split(".");
    let currentSchema: z.ZodSchema<any> = schema;

    for (const part of parts) {
        // Unwrap the schema if it's a ZodDefault, ZodOptional, ZodNullable, etc.
        let unwrappedSchema = currentSchema;
        while (
            unwrappedSchema instanceof ZodDefault ||
            unwrappedSchema instanceof ZodOptional ||
            unwrappedSchema instanceof ZodNullable
        ) {
            unwrappedSchema = unwrappedSchema._def.innerType;
        }

        // Check if the unwrapped schema is an object schema
        if (unwrappedSchema instanceof ZodObject) {
            const shape = unwrappedSchema.shape;
            // Check if the current part exists in the object's shape
            if (part in shape) {
                currentSchema = shape[part] as z.ZodSchema<any>; // Move to the next nested schema
            } else {
                return false; // Part not found in the current object
            }
        } else {
            // If a non-object schema is encountered before the path is fully traversed,
            // it means the path doesn't exist as a nested object structure.
            return false;
        }
    }
    return true;
}
