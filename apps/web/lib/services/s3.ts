export async function uploadFileToS3(
    file: File,
    presigned: { url: string; fields: Record<string, string> }
) {
    const formData = new FormData();
    Object.entries(presigned.fields).forEach(([k, v]) => {
        formData.append(k, v);
    });
    formData.append("file", file);

    const res = await fetch(presigned.url, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        throw new Error(`S3 upload failed with status ${res.status}`);
    }
}