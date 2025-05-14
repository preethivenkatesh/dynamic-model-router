## Modelcar - Serving Models Using OCI Image

This example uses [KServe's ModelCars feature](https://kserve.github.io/website/master/modelserving/storage/oci/) to fetch and serve the models and adapters using an OCI (Open Container Initiative) image. The approach allows models to be pre-packaged into a container image for easy deployment and scaling.

To build the Modelcar, you can use the provided [Containerfile](./Containerfile). It downloads the models under `/models` folder.

```bash
podman build . -t <your image registry-info>/phi2-modelcar:0.0.1
```

After you store the image in your regisry, you can update the reference in [InferenceService config](../chart/templates/vllm/vllm-inferenceservice.yaml#L33)