/**
 * Code signing script for Windows executables
 * This script integrates with electron-builder for automated signing
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * Sign Windows executable using signtool
 * @param {string} filePath - Path to the executable to sign
 * @param {Object} options - Signing options
 */
async function signWindows(filePath, options = {}) {
    const {
        certificatePath = process.env.WINDOWS_CERT_PATH,
        certificatePassword = process.env.WINDOWS_CERT_PASSWORD,
        timestampUrl = 'http://timestamp.digicert.com',
        description = 'Photo Search & Navigation',
        productName = 'Photo Search',
        companyName = 'Photo Search Team'
    } = options;

    // Check if certificate exists
    if (!certificatePath || !fs.existsSync(certificatePath)) {
        console.warn('⚠️  Windows certificate not found, skipping code signing');
        console.warn('   Set WINDOWS_CERT_PATH environment variable for production builds');
        return;
    }

    if (!certificatePassword) {
        console.warn('⚠️  Certificate password not provided, skipping code signing');
        console.warn('   Set WINDOWS_CERT_PASSWORD environment variable for production builds');
        return;
    }

    console.log(`🔐 Signing Windows executable: ${filePath}`);

    try {
        // Build signtool command
        const signtoolCmd = [
            'signtool',
            'sign',
            '/f', `"${certificatePath}"`,
            '/p', `"${certificatePassword}"`,
            '/t', `"${timestampUrl}"`,
            '/d', `"${description}"`,
            '/du', '"https://github.com/photo-search/app"',
            '/v',
            `"${filePath}"`
        ].join(' ');

        console.log('Running signtool...');
        const output = execSync(signtoolCmd, {
            encoding: 'utf8',
            stdio: 'pipe'
        });

        console.log('✅ Code signing successful');
        console.log(output);

    } catch (error) {
        console.error('❌ Code signing failed:', error.message);

        // In development, don't fail the build
        if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️  Continuing build without code signature (development mode)');
            return;
        }

        // In production, fail the build
        throw error;
    }
}

/**
 * Verify code signature
 * @param {string} filePath - Path to the signed executable
 */
async function verifySignature(filePath) {
    try {
        console.log(`🔍 Verifying signature: ${filePath}`);

        const verifyCmd = `signtool verify /pa /v "${filePath}"`;
        const output = execSync(verifyCmd, {
            encoding: 'utf8',
            stdio: 'pipe'
        });

        console.log('✅ Signature verification successful');
        console.log(output);
        return true;

    } catch (error) {
        console.error('❌ Signature verification failed:', error.message);
        return false;
    }
}

/**
 * Hook for electron-builder afterSign event
 */
async function afterSign(context) {
    const { electronPlatformName, appOutDir } = context;

    if (electronPlatformName !== 'win32') {
        return;
    }

    const exePath = path.join(appOutDir, 'Photo Search.exe');

    if (fs.existsSync(exePath)) {
        await signWindows(exePath);
        await verifySignature(exePath);
    }
}

/**
 * Development utility: Create self-signed certificate for testing
 */
async function createTestCertificate() {
    const certPath = path.join(__dirname, 'test-cert.p12');

    if (fs.existsSync(certPath)) {
        console.log('Test certificate already exists');
        return certPath;
    }

    console.log('Creating test certificate for development...');

    try {
        // This requires OpenSSL or similar tools
        const commands = [
            // Create private key
            'openssl genrsa -out test-key.pem 2048',

            // Create certificate
            'openssl req -new -x509 -key test-key.pem -out test-cert.pem -days 365 -subj "/CN=PhotoSearch Test/O=PhotoSearch Team/C=US"',

            // Convert to PKCS#12 format
            `openssl pkcs12 -export -out "${certPath}" -inkey test-key.pem -in test-cert.pem -password pass:testpassword`
        ];

        for (const cmd of commands) {
            execSync(cmd, { cwd: __dirname });
        }

        // Clean up intermediate files
        const tempFiles = ['test-key.pem', 'test-cert.pem'];
        tempFiles.forEach(file => {
            const filePath = path.join(__dirname, file);
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
            }
        });

        console.log('✅ Test certificate created');
        console.log(`Certificate: ${certPath}`);
        console.log('Password: testpassword');

        return certPath;

    } catch (error) {
        console.error('❌ Failed to create test certificate:', error.message);
        console.warn('Install OpenSSL to create test certificates');
        return null;
    }
}

module.exports = {
    signWindows,
    verifySignature,
    afterSign,
    createTestCertificate
};

// CLI usage
if (require.main === module) {
    const args = process.argv.slice(2);
    const command = args[0];
    const filePath = args[1];

    switch (command) {
        case 'sign':
            if (!filePath) {
                console.error('Usage: node sign-windows.js sign <path-to-exe>');
                process.exit(1);
            }
            signWindows(filePath).catch(console.error);
            break;

        case 'verify':
            if (!filePath) {
                console.error('Usage: node sign-windows.js verify <path-to-exe>');
                process.exit(1);
            }
            verifySignature(filePath).catch(console.error);
            break;

        case 'create-test-cert':
            createTestCertificate().catch(console.error);
            break;

        default:
            console.log('Usage:');
            console.log('  node sign-windows.js sign <path-to-exe>');
            console.log('  node sign-windows.js verify <path-to-exe>');
            console.log('  node sign-windows.js create-test-cert');
    }
}